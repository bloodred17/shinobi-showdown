import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from langchain_openrouter import ChatOpenRouter
from contracts import Outcome, Request
from helpers import answer, fixture, scripted_generate, structured
from repository import ReadOnlyRepository, validate_evidence
from runner import dispatch
from store import Store


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.revision = fixture(self.repo)
        self.state = self.root / "state"
        self.store = Store(self.state)
        self.session = self.store.create(str(self.repo), "HEAD")["id"]
        self.env = patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test-only", "SHINOBI_MODEL": "test/offline"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.store.close()
        self.temp.cleanup()

    def chat(self, query, request_id="turn", session=None):
        request = Request(request_id=request_id, operation="chat", session_id=session or self.session, query=query)
        with patch.object(ChatOpenRouter, "_generate", scripted_generate):
            return dispatch(request, self.store)

    def child(self, operation, **fields):
        request = {"version": 1, "request_id": fields.pop("request_id", "process-turn"), "operation": operation, **fields}
        env = {**os.environ, "SHINOBI_STATE_DIR": str(self.state)}
        return subprocess.run([sys.executable, str(ROOT / "tests/offline_runner.py")], input=json.dumps(request),
                              text=True, capture_output=True, timeout=30, env=env)

    def test_new_process_retains_constraint_and_sessions_are_isolated(self):
        self.chat("Keep API unchanged and remember BLUEBIRD", "first")
        result = self.child("chat", session_id=self.session, query="What constraint did I give?", request_id="followup")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("BLUEBIRD", json.loads(result.stdout)["outcome"]["message"])
        other = self.store.create(str(self.repo), "HEAD")["id"]
        self.assertNotIn("BLUEBIRD", self.chat("What constraint?", "other", other)["outcome"]["message"])

    def test_proposal_revision_and_clarification(self):
        first = self.chat("proposal cap 10", "one")
        second = self.chat("revise proposal cap 20", "two")
        self.assertEqual(first["proposal_version"], 1)
        self.assertEqual(second["proposal_version"], 2)
        self.assertEqual(second["outcome"]["proposal"]["constraints"], ["Preserve API", "Cap 20"])
        self.assertEqual(second["outcome"]["evidence"][0]["path"], "reconnect.py")
        self.assertEqual(self.chat("clarify", "three")["outcome"]["kind"], "needs_input")

    def test_failed_turn_does_not_advance_conversation_or_replay(self):
        self.chat("remember SUCCESS", "good")
        pointer = self.store.row(self.session)["checkpoint"]
        with self.assertRaisesRegex(RuntimeError, "intentional"):
            self.chat("FAIL", "failure")
        self.assertEqual(self.store.row(self.session)["checkpoint"], pointer)
        resumed = dispatch(Request(request_id="resume", operation="resume", session_id=self.session), self.store)
        self.assertEqual(resumed["history"][-1]["status"], "failed")
        next_turn = self.chat("Continue", "next")["outcome"]["message"]
        self.assertIn("SUCCESS", next_turn)
        self.assertNotIn("FAIL", next_turn)
        with self.assertRaisesRegex(ValueError, "will not be replayed"):
            self.chat("FAIL", "failure")

    def test_duplicate_completed_request_returns_result_without_model_call(self):
        first = self.chat("hello", "same")
        with patch.object(ChatOpenRouter, "_generate", side_effect=AssertionError("must not call")):
            again = dispatch(Request(request_id="same", operation="chat", session_id=self.session, query="hello"), self.store)
        self.assertTrue(again["replayed"])
        self.assertEqual({k: v for k, v in again.items() if k != "replayed"}, first)
        self.store.fail(self.session, "same", "late transport failure", "interrupted")
        self.assertEqual(self.store.previous(self.session, "same", "hello")["status"], "completed")
        with self.assertRaisesRegex(ValueError, "different input"):
            self.chat("different", "same")

    def test_snapshot_ignores_worktree_and_new_commits_and_skips_symlinks(self):
        (self.repo / "reconnect.py").write_text("dirty\n")
        (self.repo / "untracked.txt").write_text("not committed")
        (self.repo / "link").symlink_to("/etc/passwd")
        subprocess.run(["git", "-C", str(self.repo), "add", "link"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.name=Test", "-c", "user.email=t@example.invalid", "commit", "-qm", "link"], check=True)
        other = self.store.create(str(self.repo), "HEAD")
        snap = self.store.workspace(other["id"])
        self.assertIn("min(2 ** attempt, 30)", (snap / "reconnect.py").read_text())
        self.assertFalse((snap / "untracked.txt").exists())
        self.assertFalse((snap / "link").exists())
        self.assertTrue(other["dirty_at_creation"])
        self.assertEqual(self.store.info(self.session)["revision"], self.revision)

    def test_snapshot_inspection_does_not_execute_repository_fsmonitor_hook(self):
        marker = self.root / "unapproved-operation"
        hook = self.repo / ".git" / "fsmonitor-hook"
        hook.write_text("#!/usr/bin/env python3\nfrom pathlib import Path\nPath(" + repr(str(marker)) + ").write_text('executed')\nprint('monitor-token')\n")
        hook.chmod(0o755)
        subprocess.run(["git", "-C", str(self.repo), "config", "core.fsmonitor", str(hook)], check=True)
        self.store.create(str(self.repo), "HEAD")
        self.assertFalse(marker.exists())

    def test_repository_mutations_blocked_in_real_graph_and_backend(self):
        before = (self.repo / "reconnect.py").read_bytes()
        result = self.chat("write the file", "blocked-write")
        self.assertTrue(any(c["status"] == "error" for c in result["tool_calls"]))
        for tool in ["write_file", "edit_file", "delete", "task", "execute", "write_todos"]:
            self.assertNotIn(tool, result["bound_tools"])
        self.assertEqual((self.repo / "reconnect.py").read_bytes(), before)
        root = self.store.workspace(self.session)
        self.assertEqual((root / "reconnect.py").read_bytes(), before)
        backend = ReadOnlyRepository(root, [])
        self.assertIsNotNone(backend.write("/reconnect.py", "bad").error)
        self.assertIsNotNone(backend.edit("/reconnect.py", "def", "bad").error)
        self.assertIsNotNone(backend.delete("/reconnect.py").error)
        with self.assertRaises(ValueError):
            backend.read("/../outside")

    def test_citations_require_real_read_lines_and_reject_fabrication(self):
        root = self.store.workspace(self.session)
        citation = {"path": "reconnect.py", "start_line": 1, "end_line": 2, "claim": "cap"}
        outcome = Outcome.model_validate(answer("found", evidence=[citation]))
        with self.assertRaisesRegex(ValueError, "not backed"):
            validate_evidence(outcome, root, [])
        reads = []
        ReadOnlyRepository(root, reads).read("/reconnect.py")
        validate_evidence(outcome, root, reads)
        for path, end in [("missing.py", 2), ("../reconnect.py", 2), ("reconnect.py", 99)]:
            bad = Outcome.model_validate(answer("found", evidence=[{**citation, "path": path, "end_line": end}]))
            with self.assertRaises(ValueError):
                validate_evidence(bad, root, reads)
        with patch.object(ChatOpenRouter, "_generate", return_value=structured(answer("fake", evidence=[{**citation, "path": "missing.py"}]))):
            with self.assertRaisesRegex(ValueError, "unavailable"):
                dispatch(Request(request_id="fabricated", operation="chat", session_id=self.session, query="fake"), self.store)
        self.assertIsNone(self.store.row(self.session)["checkpoint"])

    def test_killed_process_and_cross_process_lock_are_reconciled_without_replay(self):
        request = {"request_id": "killed", "operation": "chat", "session_id": self.session, "query": "HANG"}
        child = subprocess.Popen([sys.executable, str(ROOT / "tests/offline_runner.py")], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 env={**os.environ, "SHINOBI_STATE_DIR": str(self.state)})
        try:
            child.stdin.write(json.dumps(request).encode()); child.stdin.close()
            for _ in range(150):
                if self.store.previous(self.session, "killed", "HANG"):
                    break
                time.sleep(0.05)
            else:
                self.fail("child never started a turn")
            with self.assertRaisesRegex(ValueError, "busy"):
                with self.store.locked(self.session):
                    pass
            os.kill(child.pid, signal.SIGKILL)
            child.wait(timeout=5)
            resumed = dispatch(Request(request_id="resume", operation="resume", session_id=self.session), self.store)
            self.assertEqual(resumed["history"][-1]["status"], "interrupted")
            self.assertIsNone(self.store.row(self.session)["checkpoint"])
            with self.assertRaisesRegex(ValueError, "will not be replayed"):
                self.chat("HANG", "killed")
            self.assertEqual(self.chat("continue", "fresh")["outcome"]["kind"], "answer")
        finally:
            if child.poll() is None:
                child.kill(); child.wait()
            child.stdout.close(); child.stderr.close()

    def test_schema_and_missing_configuration_are_errors(self):
        with self.assertRaises(ValueError):
            Request(request_id="bad", operation="chat", session_id="../escape", query="x")
        with patch.dict(os.environ, {"SHINOBI_MODEL": ""}):
            result = self.child("chat", session_id=self.session, query="hello")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)["status"], "error")
        self.assertEqual(self.store.info(self.session)["history"][-1]["status"], "failed")


if __name__ == "__main__":
    unittest.main()
