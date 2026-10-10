import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
import threading
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from langchain_openrouter import ChatOpenRouter
from contracts import Request
from execution import Context, execute_run
from execution_contracts import TaskContract
from execution_store import Runs
from execution_api import summary
from execution_helpers import scripted_execution_generate
from helpers import fixture, scripted_generate
from runner import dispatch
from sandbox import Sandbox
from store import Store
from workspace import artifact_hash, manifest, export, commit, local_git, deliver


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="shinobi-execution-")
        self.root = Path(self.temp.name)
        self.repository = self.root / "repo"
        fixture(self.repository)
        (self.repository / "limits.py").write_text("TIMEOUT = 60\n")
        (self.repository / "test_behavior.py").write_text(
            "import unittest\nfrom reconnect import retry_delay\nfrom limits import TIMEOUT\n"
            "class Behavior(unittest.TestCase):\n"
            "    def test_cap(self): self.assertEqual(retry_delay(100), 10)\n"
            "    def test_timeout(self): self.assertEqual(TIMEOUT, 20)\n")
        subprocess.run(["git", "-C", str(self.repository), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.repository), "-c", "user.name=Test", "-c", "user.email=t@example.invalid", "commit", "-qm", "checks"], check=True)
        self.store = Store(self.root / "state")
        self.session = self.store.create(str(self.repository), "HEAD")["id"]
        self.env = patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test-only", "SHINOBI_MODEL": "test/offline"})
        self.env.start()
        self.launch = patch("execution_api.launch")
        self.launch.start()
        with patch.object(ChatOpenRouter, "_generate", scripted_generate):
            dispatch(Request(operation="chat", request_id="proposal", session_id=self.session, query="proposal cap 10"), self.store)
        self.settings = {
            "checks": [{"id": "behavior", "argv": ["python3.12", "-B", "-m", "unittest", "test_behavior"]}],
            "work_items": [{"id": "cap", "instruction": "Cap delay at 10", "paths": ["reconnect.py"]},
                           {"id": "timeout", "instruction": "Cap timeout at 20", "paths": ["limits.py"]}],
            "limits": {"max_workers": 2},
        }
        # Model fixture supplies the broader, repository-grounded proposal for the two-item run.
        row = self.store.db.execute("SELECT response FROM turns WHERE session_id=?", (self.session,)).fetchone()
        response = json.loads(row["response"])
        response["outcome"]["proposal"]["affected_paths"] = ["reconnect.py", "limits.py"]
        response["outcome"]["proposal"]["acceptance_criteria"] = ["Delay caps at 10", "Timeout is 20"]
        with self.store.db:
            self.store.db.execute("UPDATE turns SET response=? WHERE session_id=?", (json.dumps(response), self.session))

    def tearDown(self):
        self.launch.stop()
        self.env.stop()
        self.store.close()
        self.temp.cleanup()

    def request(self, operation, identity=None, **fields):
        return dispatch(Request(operation=operation, request_id=identity or operation, session_id=self.session, **fields), self.store)

    def approve(self):
        contract = self.request("contract", execution=self.settings)["contract"]
        return self.request("approve", contract_hash=contract["hash"])["run"]["id"]

    def execute(self, run_id):
        with patch.object(ChatOpenRouter, "_generate", scripted_execution_generate):
            execute_run(self.store.root, run_id)
        return Runs(self.store).info(run_id)

    def test_real_parallel_graph_sandbox_checks_review_and_patch(self):
        before = manifest(self.repository)
        run_id = self.approve()
        info = self.execute(run_id)
        self.assertEqual(info["status"], "verified", info["message"])
        self.assertEqual(set(info["completed"]), {"cap", "timeout"})
        self.assertEqual(manifest(self.repository), before)
        artifact = info["artifact"]
        self.assertEqual(artifact_hash(Path(artifact["workspace"])), artifact["artifact_hash"])
        self.assertIn("-    return min(2 ** attempt, 30)", Path(artifact["patch"]).read_text())
        self.assertEqual(info["checks"][0]["artifact_hash"], artifact["artifact_hash"])
        self.assertEqual(info["checks"][0]["exit_code"], 0)
        for attempt in info["attempts"].values():
            self.assertIn("replace_source", attempt["bound_tools"])
            self.assertNotIn("task", attempt["bound_tools"])
        self.assertNotIn("replace_source", info["reviews"][-1]["bound_tools"])

    def test_approval_is_explicit_version_bound_and_duplicate_safe(self):
        with self.assertRaisesRegex(ValueError, "latest contract"):
            self.request("approve", contract_hash="0" * 64)
        first = self.request("contract", execution=self.settings)["contract"]
        second = self.request("contract", "contract2", execution=self.settings)["contract"]
        with self.assertRaisesRegex(ValueError, "latest contract"):
            self.request("approve", "stale", contract_hash=first["hash"])
        run = self.request("approve", contract_hash=second["hash"])["run"]
        replay = self.request("approve", contract_hash=second["hash"])
        self.assertTrue(replay["replayed"])
        self.assertEqual(replay["run"]["id"], run["id"])
        with self.assertRaisesRegex(ValueError, "different input"):
            self.request("approve", contract_hash=first["hash"])
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM approvals").fetchone()[0], 1)

    def test_plan_rejects_cycle_missing_dependencies_and_scope_expansion(self):
        for index, change in enumerate([
            {"depends_on": ["unknown"]}, {"depends_on": ["cap"]}, {"paths": ["outside.py"]},
        ]):
            settings = json.loads(json.dumps(self.settings))
            settings["work_items"][0].update(change)
            with self.assertRaises(ValueError):
                self.request("contract", "invalid" + str(index), execution=settings)
        with self.assertRaises(ValueError):
            self.request("contract", "no-checks", execution={**self.settings, "checks": []})

    def test_readonly_commands_network_secrets_and_scope_escape_are_blocked(self):
        workspace = self.store.workspace(self.session)
        sandbox = Sandbox(workspace)
        sandbox.preflight()
        for code in [
            "open('/workspace/reconnect.py','w').write('bad')",
            "open('/etc/passwd').read()",
            "import socket; socket.create_connection(('1.1.1.1',80),timeout=.1)",
        ]:
            result = sandbox.execute(["python3.12", "-c", code])
            self.assertNotEqual(result["exit_code"], 0)
        result = sandbox.execute(["python3.12", "-c", "import os; assert 'OPENROUTER_API_KEY' not in os.environ"])
        self.assertEqual(result["exit_code"], 0, result)
        with self.assertRaises(ValueError):
            sandbox.file("read", "../etc/passwd")
        with self.assertRaises(ValueError):
            sandbox.file("write", "AGENTS.md", scopes=["reconnect.py"], content="bad")

    def test_cancel_pause_steering_and_unavailable_sandbox_do_not_execute(self):
        run_id = self.approve()
        self.request("pause")
        self.assertEqual(self.execute(run_id)["status"], "paused")
        self.request("continue")
        self.request("cancel")
        self.assertEqual(self.execute(run_id)["status"], "cancelled")
        self.assertEqual(Runs(self.store).info(run_id)["model_calls"], 0)

    def test_unavailable_sandbox_fails_before_model_execution(self):
        run_id = self.approve()
        with patch("sandbox.shutil.which", return_value=None):
            info = self.execute(run_id)
        self.assertEqual(info["status"], "failed")
        self.assertEqual(info["model_calls"], 0)
        self.assertIsNone(info["artifact"])

    def test_steering_invalidates_authority_and_never_silently_resumes(self):
        run_id = self.approve()
        self.request("steer", query="Preserve the cap at 30")
        info = self.execute(run_id)
        self.assertEqual(info["status"], "waiting_approval")
        self.assertTrue(info["invalidated"])
        with self.assertRaises(ValueError):
            self.request("continue")
        with self.assertRaisesRegex(ValueError, "repository-grounded proposal"):
            self.request("contract", "old-proposal", execution=self.settings)
        with patch.object(ChatOpenRouter, "_generate", scripted_generate):
            revised = self.request("chat", "new-proposal", query="Revise proposal cap 20")
        self.assertIn("Preserve the cap at 30", self.store.db.execute("SELECT instruction FROM session_directions").fetchone()[0])
        self.assertGreater(revised["proposal_version"], 1)

    def test_active_cancellation_settles_workers_without_later_writes(self):
        run_id = self.approve()
        active = threading.Event()

        def delayed(model, messages, **kwargs):
            active.set()
            time.sleep(0.4)
            return scripted_execution_generate(model, messages, **kwargs)

        with patch.object(ChatOpenRouter, "_generate", delayed), ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(execute_run, self.store.root, run_id)
            self.assertTrue(active.wait(10))
            stopped = self.request("cancel")["run"]
            self.assertEqual(stopped["status"], "cancelling")
            future.result(timeout=10)
        info = Runs(self.store).info(run_id)
        self.assertEqual(info["status"], "cancelled", info["message"])
        count = self.store.db.execute("SELECT count(*) FROM run_events WHERE run_id=? AND kind='file_intent'", (run_id,)).fetchone()[0]
        self.assertEqual(count, 0)

    def test_killed_controller_reconciles_partial_work_and_recovers_explicitly(self):
        run_id = self.approve()
        child = subprocess.Popen([sys.executable, str(ROOT / "tests/offline_execution.py"), str(self.store.root), run_id, "--hang"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        try:
            deadline = time.monotonic() + 10
            while Runs(self.store).info(run_id)["model_calls"] == 0:
                if time.monotonic() > deadline:
                    self.fail("Detached controller never started a model call")
                time.sleep(0.05)
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=5)
        finally:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait(timeout=5)
        status = self.request("status")["run"]
        self.assertEqual(status["status"], "interrupted")
        calls = Runs(self.store).info(run_id)["model_calls"]
        self.assertEqual(Runs(self.store).info(run_id)["model_calls"], calls)
        self.request("recover")
        info = self.execute(run_id)
        self.assertEqual(info["status"], "verified", info["message"])
        self.assertEqual(info["replans"], 1)

    def test_model_budget_is_enforced_before_exceeding_approved_calls(self):
        self.settings["limits"]["model_calls"] = 1
        run_id = self.approve()
        info = self.execute(run_id)
        self.assertEqual(info["status"], "failed")
        self.assertEqual(info["model_calls"], 1)
        self.assertIsNone(info["artifact"])

    def test_missing_assurance_coverage_prevents_verified_delivery(self):
        run_id = self.approve()
        from langchain_core.messages import AIMessage
        from helpers import output

        def incomplete(model, messages, **kwargs):
            if any("independent assurance reviewer" in str(m.content) for m in messages):
                return output(AIMessage(content="", tool_calls=[{"name": "Review", "args": {
                    "verdict": "pass", "summary": "Trust me", "findings": [], "coverage": []}, "id": "bad-pass"}]))
            return scripted_execution_generate(model, messages, **kwargs)

        with patch.object(ChatOpenRouter, "_generate", incomplete):
            execute_run(self.store.root, run_id)
        info = Runs(self.store).info(run_id)
        self.assertEqual(info["status"], "failed")
        self.assertIsNone(info["artifact"])

    def test_localized_repair_retains_unaffected_completed_worker(self):
        self.settings["checks"][0]["affected_items"] = ["cap"]
        run_id = self.approve()
        wrong_once = False
        lock = threading.Lock()

        def faulty_then_repair(model, messages, **kwargs):
            nonlocal wrong_once
            result = scripted_execution_generate(model, messages, **kwargs)
            for call in result.generations[0].message.tool_calls:
                if call["name"] == "replace_source" and call["args"]["path"] == "reconnect.py":
                    with lock:
                        if not wrong_once:
                            wrong_once = True
                            call["args"]["new"] = "11"
                        else:
                            call["args"]["old"] = "11"
            return result

        with patch.object(ChatOpenRouter, "_generate", faulty_then_repair):
            execute_run(self.store.root, run_id)
        info = Runs(self.store).info(run_id)
        self.assertEqual(info["status"], "verified", info["message"])
        self.assertEqual(info["repair_cycle"], 1)
        self.assertEqual(sum(a["item"] == "timeout" for a in info["attempts"].values()), 1)
        self.assertEqual(sum(a["item"] == "cap" for a in info["attempts"].values()), 2)

    def test_dependencies_are_scheduled_before_dependents(self):
        self.settings["work_items"][1]["depends_on"] = ["cap"]
        run_id = self.approve()
        info = self.execute(run_id)
        self.assertEqual(info["status"], "verified", info["message"])
        scheduled = [json.loads(e["data"])["items"] for e in self.store.db.execute(
            "SELECT data FROM run_events WHERE run_id=? AND kind='scheduled' ORDER BY seq", (run_id,))]
        self.assertEqual(scheduled, [["cap"], ["timeout"]])

    def test_overlapping_worker_ownership_is_serialized(self):
        self.settings["work_items"][1]["paths"] = ["limits.py", "reconnect.py"]
        run_id = self.approve()
        info = self.execute(run_id)
        self.assertEqual(info["status"], "verified", info["message"])
        scheduled = [json.loads(e["data"])["items"] for e in self.store.db.execute(
            "SELECT data FROM run_events WHERE run_id=? AND kind='scheduled' ORDER BY seq", (run_id,))]
        self.assertEqual(scheduled, [["cap"], ["timeout"]])

    def test_symlink_escape_is_rejected_even_for_owned_path(self):
        workspace = self.store.workspace(self.session)
        (workspace / "link.txt").symlink_to("/etc/passwd")
        with self.assertRaises(ValueError):
            Sandbox(workspace).file("read", "link.txt")

    def test_git_artifact_preserves_tracked_ignored_files_binary_modes_and_exact_bytes(self):
        (self.repository / ".gitignore").write_text("ignored.txt\n")
        (self.repository / ".gitattributes").write_text("*.txt text eol=lf\n")
        (self.repository / "ignored.txt").write_bytes(b"original\r\n")
        (self.repository / "blob.bin").write_bytes(b"\x00\xff\x01")
        (self.repository / "executable").write_text("#!/usr/bin/env python3\n")
        (self.repository / "executable").chmod(0o755)
        # Import the deliberately non-normalized fixture through the same raw Git plumbing.
        revision = commit(self.repository, "exact-byte source")
        copy = self.root / "exact-copy"
        export(str(self.repository), revision, copy)
        self.assertEqual(local_git(copy, "rev-parse", "HEAD^{tree}"), local_git(self.repository, "rev-parse", "HEAD^{tree}"))
        self.assertEqual(manifest(copy), manifest(self.repository))
        (copy / "ignored.txt").write_bytes(b"changed\r\n")
        commit(copy, "raw change")
        self.assertEqual(local_git(copy, "show", "HEAD:ignored.txt"), b"changed\r\n")
        artifact = deliver(copy, self.root, revision)
        check = subprocess.run(["git", "-C", str(self.repository), "apply", "--check", artifact["patch"]], capture_output=True)
        self.assertEqual(check.returncode, 0, check.stderr.decode())

    def test_failed_checks_cannot_be_overridden_by_reviewer_and_repairs_are_bounded(self):
        self.settings["checks"][0]["argv"] = ["python3.12", "-c", "raise SystemExit(1)"]
        run_id = self.approve()
        info = self.execute(run_id)
        self.assertEqual(info["status"], "failed")
        self.assertEqual(info["repair_cycle"], 2)
        self.assertEqual(info["reviews"], [])
        self.assertIsNone(info["artifact"])

    def test_changed_source_or_artifact_requires_new_approval(self):
        contract = self.request("contract", execution=self.settings)["contract"]
        subprocess.run(["git", "-C", str(self.repository), "-c", "user.name=Test", "-c", "user.email=t@example.invalid", "commit", "--allow-empty", "-qm", "new baseline"], check=True)
        with self.assertRaisesRegex(ValueError, "Source HEAD changed"):
            self.request("approve", contract_hash=contract["hash"])

    def test_artifact_tampering_invalidates_verified_evidence(self):
        run_id = self.approve()
        info = self.execute(run_id)
        self.assertEqual(info["status"], "verified", info["message"])
        (Path(info["workspace"]) / "reconnect.py").write_text("tampered")
        status = self.request("status")["run"]
        self.assertEqual(status["status"], "waiting_approval")
        self.assertTrue(status["invalidated"])


if __name__ == "__main__":
    unittest.main()
