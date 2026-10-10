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

MATH_QUERY = "What is 17 + 25? Reply with the number only."
FILE_QUERY = (
    "Read /input.txt. Write /result.txt containing the unique non-empty lines "
    "sorted alphabetically, one per line. Read the result back and tell me how "
    "many lines it contains."
)


class PiTui:
    def __init__(self, folder: Path, *, fake: bool, fixture="default", bridge=True):
        self.folder = folder
        folder.mkdir(parents=True)
        self.log = folder / "guard.jsonl"
        self.session = folder / "session.jsonl"
        self.output = bytearray()
        self.last_snapshot = 0
        self.query_timeout = 10 if fake else 125
        env = dict(os.environ)
        env.update(
            PI_CODING_AGENT_DIR=str(folder / "profile"),
            PI_TELEMETRY="0", TERM="xterm-256color",
            SHINOBI_POC_GUARD_LOG=str(self.log), SHINOBI_POC_FIXTURE=fixture,
        )
        if fake:
            # The fake TUI smoke has no provider credentials, including OpenRouter.
            env = {key: value for key, value in env.items() if not any(
                marker in key for marker in ("API_KEY", "AUTH_TOKEN", "OAUTH_TOKEN", "ACCESS_KEY", "SECRET_KEY")
            )}
            env["SHINOBI_POC_PYTHON"] = str(ROOT / "tests/fake-python.py")
        else:
            env["SHINOBI_POC_PYTHON"] = str(ROOT / ".venv/bin/python")
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
                if x.get("type") == "displayed" and x.get("message", {}).get("customType") == "shinobi-poc"]

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

    def query(self, text, timeout=None):
        count = len(self.messages())
        self.type(text)
        self.wait(lambda: len(self.messages()) > count, timeout or self.query_timeout)
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
            assert f"Workspace: {result['workspace']}" in rendered
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


def verify_file_result(result, expected):
    assert result["status"] == "ok", result.get("error")
    workspace = Path(result["workspace"])
    actual = (workspace / "result.txt").read_text()
    assert actual.removesuffix("\n") == expected, (actual, expected)
    assert workspace.parent == Path("/tmp")
    calls = result["tool_calls"]
    ordered = []
    for call in calls:
        assert call["name"] not in {"task", "execute", "write_todos"}, call
        if call["status"] != "ok":
            continue
        args = json.loads(call["input"])
        if isinstance(args, str):
            args = json.loads(args)
        path = args.get("file_path", "")
        if call["name"] == "read_file" and path == "/input.txt":
            ordered.append("input")
        if call["name"] == "write_file" and path == "/result.txt":
            ordered.append("write")
        if call["name"] == "read_file" and path == "/result.txt":
            ordered.append("readback")
    assert "input" in ordered and "write" in ordered and "readback" in ordered, calls
    assert ordered.index("input") < ordered.index("write") < ordered.index("readback"), calls
    assert result["model_calls"] and all(x == result["model"] for x in result["model_calls"]), result["model_calls"]
    assert "task" not in result["bound_tools"]
    return {"workspace": str(workspace), "content": actual, "ordered_tools": ordered}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.live:
        try:
            runner.configuration()
        except runner.ConfigurationError as exc:
            print(json.dumps({"verdict": "blocked", "reason": str(exc)}))
            return 2
    folder = Path(tempfile.mkdtemp(prefix="shinobi-pi-smoke-", dir="/tmp"))
    report = {"mode": "live" if args.live else "fake-bridge-only", "evidence": str(folder), "checks": []}
    try:
        # Negative control: the exact guard selected below detects native inference.
        control = PiTui(folder / "control", fake=True, bridge=False)
        try:
            control.type("Trigger the fail-on-call provider.")
            control.wait(lambda: any(x["type"] == "native_model_call" for x in control.events()))
            report["checks"].append("fail-on-call provider negative control passed")
        finally:
            control.close()

        if args.live:
            completed = subprocess.run(
                [str(ROOT / ".venv/bin/python"), str(ROOT / "runner.py")],
                input=json.dumps({"request_id": "direct-backend", "query": FILE_QUERY}),
                text=True, capture_output=True, timeout=125,
            )
            direct = json.loads(completed.stdout)
            (folder / "direct.json").write_text(json.dumps(direct, indent=2))
            assert completed.returncode == 0, direct.get("error")
            report["direct"] = verify_file_result(direct, "apple\nbanana\npear")

        tui = PiTui(folder / "default", fake=not args.live)
        try:
            message = tui.query(MATH_QUERY)
            result = message["details"]["result"]
            assert result["answer"].strip() == "42", result
            report["checks"].append("typed Pi arithmetic response displayed")
            if args.live:
                message = tui.query(FILE_QUERY)
                result = message["details"]["result"]
                report["file"] = verify_file_result(result, "apple\nbanana\npear")
                assert "3" in result["answer"] or "three" in result["answer"].lower()
                assert message["details"]["query"] == FILE_QUERY
                assert result["workspace"].encode() in tui.output
            else:
                assert result["received_query"] == MATH_QUERY
                failed = tui.query("FAKE_MALFORMED")
                assert "malformed JSON" in failed["content"]
                recovered = tui.query(MATH_QUERY)
                assert recovered["details"]["result"]["answer"] == "42"
                tui.type("FAKE_SLOW")
                tui.wait(lambda: any(x.get("query") == "FAKE_SLOW" for x in tui.events()))
                busy = tui.query("second concurrent input")
                assert "Busy:" in busy["content"]
                tui.wait(lambda: any(x.get("details", {}).get("result", {}).get("received_query") == "FAKE_SLOW" for x in tui.messages()))
                report["checks"].append("malformed response recovery and busy rejection passed")
            report["pi_native_inference"] = tui.proof()
            assert all(x["source"] == "interactive" for x in tui.events() if x["type"] == "input")
        finally:
            tui.close()

        if args.live:
            changed = PiTui(folder / "changed", fake=False, fixture="changed")
            try:
                message = changed.query(FILE_QUERY)
                result = message["details"]["result"]
                report["changed_file"] = verify_file_result(result, "kiwi\nzebra")
                assert "2" in result["answer"] or "two" in result["answer"].lower()
                assert report["changed_file"]["workspace"] != report["file"]["workspace"]
                changed.proof()
            finally:
                changed.close()
        report["verdict"] = "proven" if args.live else "partially proven"
    except Exception as exc:
        report.update(verdict="failed", error=runner.sanitize(str(exc)))
    (folder / "report.json").write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if report["verdict"] != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
