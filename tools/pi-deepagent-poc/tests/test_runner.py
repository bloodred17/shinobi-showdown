import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import runner
from deepagents.backends import FilesystemBackend


class RunnerTests(unittest.TestCase):
    def test_missing_model_key_invalid_model_and_excluded_families(self):
        for env, expected in [
            ({}, "SHINOBI_POC_MODEL"),
            ({"SHINOBI_POC_MODEL": "test/model"}, "OPENROUTER_API_KEY"),
            ({"SHINOBI_POC_MODEL": "not-an-id"}, "vendor/model"),
            ({"SHINOBI_POC_MODEL": "openai/model"}, "excluded"),
            ({"SHINOBI_POC_MODEL": "anthropic/model"}, "excluded"),
            ({"SHINOBI_POC_MODEL": "openrouter/auto"}, "excluded"),
        ]:
            with self.subTest(env=env), patch.dict(os.environ, env, clear=True):
                with self.assertRaisesRegex(runner.ConfigurationError, expected):
                    runner.configuration()

    def test_missing_key_returns_one_error_json_and_nonzero_exit(self):
        env = {"PATH": os.environ["PATH"], "SHINOBI_POC_MODEL": "test/model"}
        completed = subprocess.run(
            [sys.executable, str(Path(runner.__file__))],
            input=json.dumps({"request_id": "missing-key", "query": "hello"}),
            text=True, capture_output=True, env=env, timeout=5,
        )
        result = json.loads(completed.stdout)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(result["request_id"], "missing-key")
        self.assertEqual(result["status"], "error")
        self.assertIn("OPENROUTER_API_KEY", result["error"])
        self.assertEqual(len(completed.stdout.splitlines()), 1)

    def test_real_filesystem_tools_restrict_parent_and_symlink_escape(self):
        with tempfile.TemporaryDirectory() as scratch, tempfile.TemporaryDirectory() as outside:
            backend = FilesystemBackend(root_dir=scratch, virtual_mode=True)
            self.assertIsNone(backend.write("/safe.txt", "actual file\n").error)
            self.assertEqual(Path(scratch, "safe.txt").read_text(), "actual file\n")
            self.assertIsNone(backend.read("/safe.txt").error)
            Path(outside, "secret.txt").write_text("outside sentinel")
            Path(scratch, "escape").symlink_to(outside, target_is_directory=True)
            for path in ("../escape.txt", "/../escape.txt", "/escape/secret.txt"):
                with self.subTest(path=path):
                    with self.assertRaises(ValueError):
                        backend.read(path)
                    with self.assertRaises(ValueError):
                        backend.write(path, "must not write")
            self.assertEqual(Path(outside, "secret.txt").read_text(), "outside sentinel")
            self.assertFalse(Path(outside, "escape.txt").exists())
            # A tilde is a literal virtual directory, never the user's home.
            self.assertIsNone(backend.write("~/inside.txt", "inside").error)
            self.assertEqual(Path(scratch, "~", "inside.txt").read_text(), "inside")

    def test_constructed_real_agent_has_file_tools_and_no_delegation_or_shell(self):
        with tempfile.TemporaryDirectory() as scratch, patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test-only"}):
            agent = runner.make_agent("test/offline-tool-config", Path(scratch))
            tools = agent.get_graph().nodes["tools"].data.tools_by_name
            self.assertIn("read_file", tools)
            self.assertIn("write_file", tools)
            self.assertNotIn("task", tools)
            # The dispatch node includes an execute stub. Verify actual model
            # exposure after middleware, with model generation replaced offline.
            from langchain_core.messages import AIMessage
            from langchain_core.outputs import ChatGeneration, ChatResult
            from langchain_openrouter import ChatOpenRouter
            evidence = runner.evidence_collector()
            output = ChatResult(generations=[ChatGeneration(message=AIMessage(content="offline check"))])
            with patch.object(ChatOpenRouter, "_generate", return_value=output):
                agent.invoke({"messages": [{"role": "user", "content": "offline check"}]}, config={"recursion_limit": 30, "callbacks": [evidence]})
            self.assertIn("read_file", evidence.bound_tools)
            self.assertNotIn("task", evidence.bound_tools)
            self.assertNotIn("execute", evidence.bound_tools)
            self.assertNotIn("write_todos", evidence.bound_tools)
            self.assertEqual(evidence.models, ["test/offline-tool-config"])

    def test_tool_evidence_records_real_graph_execution_with_offline_model(self):
        from langchain_core.messages import AIMessage
        from langchain_core.outputs import ChatGeneration, ChatResult
        from langchain_openrouter import ChatOpenRouter
        scripted = [
            AIMessage(content="", tool_calls=[{"name": "read_file", "args": {"file_path": "/input.txt"}, "id": "read-input"}]),
            AIMessage(content="", tool_calls=[{"name": "write_file", "args": {"file_path": "/result.txt", "content": "apple\npear\n"}, "id": "write-result"}]),
            AIMessage(content="", tool_calls=[{"name": "read_file", "args": {"file_path": "/result.txt"}, "id": "readback"}]),
            AIMessage(content="Two lines."),
        ]
        outputs = [ChatResult(generations=[ChatGeneration(message=message)]) for message in scripted]
        with tempfile.TemporaryDirectory() as scratch, patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline-test-only"}):
            Path(scratch, "input.txt").write_text("pear\napple\npear\n")
            evidence = runner.evidence_collector()
            agent = runner.make_agent("test/offline-evidence", Path(scratch))
            with patch.object(ChatOpenRouter, "_generate", side_effect=outputs):
                agent.invoke({"messages": [{"role": "user", "content": "Offline callback transport check"}]}, config={"recursion_limit": 30, "callbacks": [evidence]})
            self.assertEqual(Path(scratch, "result.txt").read_text(), "apple\npear\n")
            self.assertEqual([call["name"] for call in evidence.calls], ["read_file", "write_file", "read_file"])
            self.assertTrue(all(call["status"] == "ok" for call in evidence.calls))
            self.assertEqual(json.loads(evidence.calls[0]["input"])["file_path"], "/input.txt")
            self.assertIn("pear", evidence.calls[-1]["output"])


if __name__ == "__main__":
    unittest.main()
