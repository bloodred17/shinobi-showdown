"""Drive ordinary typed input through the pinned Pi TUI using a real PTY."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import pty
import re
import select
import signal
import struct
import subprocess
import sys
import tempfile
import termios
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import runner



class PiTui:
    def __init__(self, folder: Path, *, fake: bool, repository: Path, state: Path, resume=None, bridge=True):
        self.folder = folder
        folder.mkdir(parents=True)
        self.log = folder / "guard.jsonl"
        self.session = folder / "session.jsonl"
        self.output = bytearray()
        self.last_snapshot = 0
        self.query_timeout = 35 if fake else 125
        env = dict(os.environ)
        env.update(
            PI_CODING_AGENT_DIR=str(folder / "profile"),
            PI_TELEMETRY="0", TERM="xterm-256color",
            SHINOBI_POC_GUARD_LOG=str(self.log), SHINOBI_REPOSITORY=str(repository),
            SHINOBI_STATE_DIR=str(state),
        )
        if fake:
            # The fake TUI smoke has no provider credentials, including OpenRouter.
            env = {key: value for key, value in env.items() if not any(
                marker in key for marker in ("API_KEY", "AUTH_TOKEN", "OAUTH_TOKEN", "ACCESS_KEY", "SECRET_KEY")
            )}
            env["SHINOBI_PYTHON"] = str(ROOT / "tests/offline-python.py")
            env["OPENROUTER_API_KEY"] = "offline-test-only"
            env["SHINOBI_MODEL"] = "test/offline"
        else:
            env["SHINOBI_PYTHON"] = str(ROOT / ".venv/bin/python")
        env.pop("SHINOBI_SESSION_ID", None)
        if resume:
            env["SHINOBI_SESSION_ID"] = resume
        command = [
            "node", str(ROOT / "node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js"),
            "--offline", "--approve", "--no-tools", "--no-extensions", "--no-skills",
            "--no-prompt-templates", "--no-context-files", "--no-themes",
            "--provider", "poc-guard", "--model", "fail-on-call", "--thinking", "off",
            "--session", str(self.session), "-e", str(ROOT / "tests/inference-guard.ts"),
        ]
        if bridge:
            command.extend(["-e", str(ROOT / "extension.ts")])
        self.master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 140, 0, 0))
        self.child = subprocess.Popen(
            command, cwd=ROOT, env=env, stdin=slave, stdout=slave, stderr=slave,
            start_new_session=True,
        )
        os.close(slave)
        try:
            self.wait(lambda: any(x["type"] == "ready" for x in self.events()), 15)
            self.wait(lambda: b"fail-on-call" in self.output, 10)
            self.pump(0.5)
        except BaseException:
            self.close()
            raise

    def events(self):
        return self.read_jsonl(self.log)

    @staticmethod
    def read_jsonl(path):
        if not path.exists():
            return []
        values = []
        for line in path.read_text().splitlines():
            try:
                values.append(json.loads(line))
            except ValueError:
                pass  # A final line may still be in the process of being appended.
        return values

    def messages(self):
        # Pi 0.84.4 defers session-file creation until a native assistant message.
        # Capture its public in-memory session entries; no native turn is needed.
        if time.monotonic() - self.last_snapshot >= 0.2:
            self.type("/poc-snapshot")
            self.last_snapshot = time.monotonic()
        return [x["message"] for x in self.events()
                if x.get("type") == "displayed" and x.get("message", {}).get("customType") == "shinobi"]

    def pump(self, duration=0.05):
        deadline = time.monotonic() + duration
        while time.monotonic() < deadline:
            if select.select([self.master], [], [], 0.02)[0]:
                try:
                    data = os.read(self.master, 65536)
                except OSError:
                    return
                self.output.extend(data)
                if len(self.output) > 2 * 1024 * 1024:
                    raise AssertionError("Pi TUI capture exceeded 2 MiB")
                if b"\x1b[6n" in data:
                    os.write(self.master, b"\x1b[1;1R")

    def wait(self, predicate, timeout=10):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.pump()
            if predicate():
                return
            if self.child.poll() is not None:
                raise AssertionError(f"Pi exited early with {self.child.returncode}; see {self.folder}/tui.txt")
        raise AssertionError(f"Timed out waiting for Pi; see {self.folder}/tui.txt")

    def type(self, text):
        os.write(self.master, text.encode() + b"\r")

    def query(self, text, timeout=None, outcome=True):
        count = len(self.messages())
        self.type(text)
        self.wait(lambda: any((not outcome or m.get("details", {}).get("result", {}).get("outcome") or m.get("details", {}).get("status") == "error") for m in self.messages()[count:]), timeout or self.query_timeout)
        self.pump(0.3)
        message = self.messages()[-1]
        rendered = re.sub(
            r"\x1b\][^\x07]*(?:\x07|\x1b\\)|\x1b\[[0-?]*[ -/]*[@-~]",
            "", self.output.decode(errors="replace"),
        )
        rendered = " ".join(rendered.split())
        result = message.get("details", {}).get("result")
        if result:
            assert f"Request: {result['request_id']}" in rendered
            if result.get("session"):
                assert f"Session: {result['session']['id']}" in rendered
        else:
            assert " ".join(message["content"].split()) in rendered
        return message

    def proof(self):
        self.type("/poc-proof")
        self.wait(lambda: any(x["type"] == "proof" for x in self.events()))
        proof = [x for x in self.events() if x["type"] == "proof"][-1]
        assert proof["calls"] == 0, proof
        assert not any(x["type"] == "native_model_call" for x in self.events())
        return proof

    def close(self):
        if self.child.poll() is None:
            # Ask the TUI to exit normally so extension shutdown runs.
            try:
                os.write(self.master, b"\x04")
                self.child.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                os.killpg(self.child.pid, signal.SIGTERM)
                try:
                    self.child.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(self.child.pid, signal.SIGKILL)
                    self.child.wait(timeout=3)
        self.pump(0.05)
        # Keep a sanitized terminal capture. Never store raw environment data.
        (self.folder / "tui.txt").write_text(runner.sanitize(self.output.decode(errors="replace")))
        os.close(self.master)


def main():
    from helpers import fixture
    from agent import configuration
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.live:
        try:
            configuration()
        except ValueError as exc:
            print(json.dumps({"verdict": "blocked", "reason": str(exc)}))
            return 2
    folder = Path(tempfile.mkdtemp(prefix="shinobi-session-smoke-", dir="/tmp"))
    repository, state = folder / "fixture", folder / "state"
    revision = fixture(repository)
    original = (repository / "reconnect.py").read_bytes()
    report = {"mode": "live" if args.live else "scripted-model-real-runtime", "evidence": str(folder), "checks": []}
    try:
        control = PiTui(folder / "control", fake=True, repository=repository, state=state, bridge=False)
        try:
            control.type("Trigger native inference")
            control.wait(lambda: any(x["type"] == "native_model_call" for x in control.events()))
            report["checks"].append("native inference negative control")
        finally:
            control.close()
        tui = PiTui(folder / "first", fake=not args.live, repository=repository, state=state)
        try:
            query = "Inspect retry_delay in reconnect.py and produce a proposal to cap its delay at 10. Preserve the public API."
            result = tui.query(query)["details"]["result"]
            assert result["outcome"]["kind"] == "proposal", result
            assert result["proposal_version"] == 1
            assert result["session"]["revision"] == revision
            assert result["outcome"]["evidence"], result
            assert any(c["name"] == "read_file" and c["status"] == "ok" for c in result["tool_calls"])
            session_id = result["session"]["id"]
            report["session_id"] = session_id
            report["proposal1"] = result
            revised = tui.query("Revise the proposal: use a cap of 20 instead. Keep the public API unchanged.")["details"]["result"]
            assert revised["proposal_version"] == 2, revised
            assert "20" in json.dumps(revised["outcome"]["proposal"])
            assert revised["session"]["id"] == session_id
            report["proposal2"] = revised
            report["checks"].extend(["repository-grounded proposal", "follow-up proposal revision"])
            tui.proof()
        finally:
            tui.close()
        # Restart Pi and Python, then continue from backend state, not Pi transcript replay.
        resumed = PiTui(folder / "resumed", fake=not args.live, repository=repository, state=state, resume=session_id)
        try:
            resumed.wait(lambda: any(m.get("details", {}).get("result", {}).get("history") for m in resumed.messages()), 35)
            answer = resumed.query("What cap and API constraint did we settle on? Answer without a new proposal.")["details"]["result"]
            assert answer["session"]["id"] == session_id
            assert "20" in answer["outcome"]["message"], answer
            assert "API" in answer["outcome"]["message"] or "api" in answer["outcome"]["message"], answer
            report["resumed_answer"] = answer
            report["checks"].append("Pi restart retains latest constraints")
            if not args.live:
                failure = resumed.query("FAIL")
                assert failure["details"]["status"] == "error"
                status = resumed.query("/shinobi-session", outcome=False)["details"]["result"]
                assert status["history"][-1]["status"] == "failed"
                following = resumed.query("Continue after the failed turn")["details"]["result"]
                assert '"FAIL"' not in following["outcome"]["message"]
                report["checks"].append("failed turn visible and excluded from next conversation")
            blocked = resumed.query("Write the proposed change to reconnect.py now.")["details"]["result"]
            for tool in ("write_file", "edit_file", "delete", "execute", "task", "write_todos"):
                assert tool not in blocked["bound_tools"], blocked
            assert (repository / "reconnect.py").read_bytes() == original
            assert (state / "sessions" / session_id / "repository/reconnect.py").read_bytes() == original
            report["checks"].append("repository remains unchanged")
            resumed.proof()
        finally:
            resumed.close()
        report["checks"].append("zero Pi-native model calls in both backend sessions")
        report["verdict"] = "passed"
    except Exception as exc:
        report.update(verdict="failed", error=runner.sanitize(str(exc)))
    (folder / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({"verdict": report["verdict"], "mode": report["mode"], "report": str(folder / "report.json"), "error": report.get("error")}))
    return 0 if report["verdict"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
