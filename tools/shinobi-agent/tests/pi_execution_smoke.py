"""Actual Pi approval -> detached backend -> sandbox -> reviewed local deliverable."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from agent import configuration, sanitize
from execution_api import summary
from execution_store import Runs
from helpers import fixture
from pi_smoke import PiTui
from store import Store
from workspace import artifact_hash, manifest


def command(tui, text, predicate):
    count = len(tui.messages())
    tui.type(text)
    tui.wait(lambda: any(predicate(m.get("details", {}).get("result", {})) or m.get("details", {}).get("status") == "error"
                         for m in tui.messages()[count:]), tui.query_timeout)
    values = tui.messages()[count:]
    errors = [m for m in values if m.get("details", {}).get("status") == "error"]
    if errors:
        raise AssertionError(errors[-1]["content"])
    return next(m["details"]["result"] for m in values if predicate(m.get("details", {}).get("result", {})))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.live:
        configuration()
    folder = Path(tempfile.mkdtemp(prefix="shinobi-execution-pi-", dir="/tmp"))
    repository, state = folder / "fixture", folder / "state"
    fixture(repository)
    (repository / "limits.py").write_text("TIMEOUT = 60\n")
    (repository / "test_behavior.py").write_text(
        "import unittest\nfrom reconnect import retry_delay\nfrom limits import TIMEOUT\n"
        "class Behavior(unittest.TestCase):\n"
        "    def test_cap(self):\n        self.assertEqual(retry_delay(100), 10)\n        self.assertEqual(retry_delay(0), 1)\n"
        "    def test_timeout(self): self.assertEqual(TIMEOUT, 20)\n")
    subprocess.run(["git", "-C", str(repository), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repository), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "acceptance fixture"], check=True)
    before = manifest(repository)
    report = {"mode": "live" if args.live else "scripted-model-real-runtime", "checks": [], "folder": str(folder)}
    store = Store(state)
    run_id = None
    tui = None
    try:
        # The fail-on-call provider is selected without usable Pi inference credentials.
        control = PiTui(folder / "control", fake=True, repository=repository, state=state, bridge=False)
        try:
            control.type("Trigger native inference")
            control.wait(lambda: any(e["type"] == "native_model_call" for e in control.events()))
            report["checks"].append("native inference negative control")
        finally:
            control.close()
        tui = PiTui(folder / "first", fake=not args.live, repository=repository, state=state)
        query = "Inspect reconnect.py, limits.py, AGENTS.md and test_behavior.py. Produce a proposal to cap retry_delay at 10 and TIMEOUT at 20. Preserve the public API. Writable scope is exactly reconnect.py and limits.py. Exclude dependencies and publication. The existing unittest checks are the acceptance gate. No unresolved product decisions remain."
        proposal = tui.query(query)["details"]["result"]
        assert proposal["outcome"]["kind"] == "proposal", proposal
        session = proposal["session"]["id"]
        report.update(query=query, proposal=proposal, session_id=session)
        assert manifest(repository) == before
        settings = {
            "checks": [{"id": "behavior", "argv": ["python3.12", "-B", "-m", "unittest", "test_behavior"], "timeout_seconds": 60}],
            "work_items": [{"id": "cap", "instruction": "Cap retry_delay at 10 without changing the function signature or low-attempt behavior", "paths": ["reconnect.py"]},
                           {"id": "timeout", "instruction": "Set TIMEOUT to 20", "paths": ["limits.py"]}],
            "limits": {"max_workers": 2, "wall_seconds": 900, "model_calls": 60},
        }
        contract = command(tui, "/shinobi-contract " + json.dumps(settings), lambda r: bool(r.get("contract")))["contract"]
        report["contract"] = contract
        assert store.db.execute("SELECT count(*) FROM approvals").fetchone()[0] == 0
        assert manifest(repository) == before
        report["checks"].append("proposal and contract cannot authorize writes")
        tui.proof()
        approved = command(tui, "/shinobi-approve " + contract["hash"], lambda r: bool(r.get("run")))
        run_id = approved["run"]["id"]
        report["run_id"] = run_id
        report["state_before_pi_close"] = Runs(store).info(run_id)["status"]
        tui.close()
        tui = None
        # Pi is absent while the independent controller reaches its terminal artifact.
        deadline = time.monotonic() + (600 if args.live else 40)
        runs = Runs(store)
        while runs.info(run_id)["status"] not in {"verified", "failed", "waiting_approval", "cancelled"}:
            if time.monotonic() > deadline:
                raise AssertionError("Detached execution timed out")
            time.sleep(0.2)
        info = runs.info(run_id)
        assert info["status"] == "verified", info["message"]
        report["checks"].append("execution completed with Pi closed")
        artifact = info["artifact"]
        workspace = Path(artifact["workspace"])
        assert "min(2 ** attempt, 10)" in (workspace / "reconnect.py").read_text()
        assert (workspace / "limits.py").read_text().strip() == "TIMEOUT = 20"
        assert manifest(repository) == before
        assert artifact_hash(workspace) == artifact["artifact_hash"]
        assert all(c["exit_code"] == 0 and c["artifact_hash"] == artifact["artifact_hash"] for c in info["checks"])
        assert info["reviews"][-1]["verdict"] == "pass"
        patch_check = subprocess.run(["git", "-C", str(repository), "apply", "--check", artifact["patch"]], capture_output=True)
        assert patch_check.returncode == 0, patch_check.stderr.decode()
        report.update(artifact=artifact, verification=info["checks"], assurance=info["reviews"], attempts=info["attempts"], model_calls=info["model_calls"])
        report["checks"].extend(["two isolated workers and serialized integration", "combined behavior checks", "independent read-only review", "patch applies to unchanged source", "artifact-bound evidence"])
        resumed = PiTui(folder / "resumed", fake=not args.live, repository=repository, state=state, resume=session)
        tui = resumed
        resumed.wait(lambda: any(m.get("details", {}).get("result", {}).get("run", {}).get("status") == "verified" for m in resumed.messages()), 35)
        resumed.proof()
        report["checks"].extend(["Pi restart reconnects to verified deliverable", "zero Pi native model calls"])
        report["verdict"] = "passed"
    except Exception as exc:
        report.update(verdict="failed", error=sanitize(str(exc)))
        if run_id:
            report["run"] = summary(Runs(store), run_id)
    finally:
        if tui:
            tui.close()
        if run_id:
            runs = Runs(store)
            if runs.info(run_id)["status"] not in {"verified", "failed", "waiting_approval", "cancelled"}:
                with runs.transaction():
                    runs.control(run_id, "cancel")
        store.close()
    (folder / "report.json").write_text(sanitize(json.dumps(report, indent=2)))
    print(json.dumps({"verdict": report["verdict"], "report": str(folder / "report.json"), "error": report.get("error")}))
    return 0 if report["verdict"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
