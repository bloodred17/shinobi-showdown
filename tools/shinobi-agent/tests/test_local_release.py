"""Adversarial acceptance for the approved local S1-S5 increment."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from langchain_openrouter import ChatOpenRouter

import test_execution
from execution_contracts import BoundaryFailure, WorkerReport, digest
from execution_store import Runs
from profiles import capture_environment
from execution_helpers import scripted_execution_generate
from helpers import scripted_generate
from contracts import Request
from runner import dispatch
from workflows import GUIDANCE
from workspace import commit, manifest


class LocalReleaseTests(unittest.TestCase):
    setUp = test_execution.ExecutionTests.setUp
    tearDown = test_execution.ExecutionTests.tearDown
    request = test_execution.ExecutionTests.request
    approve = test_execution.ExecutionTests.approve
    execute = test_execution.ExecutionTests.execute

    def proposal(self, **fields):
        row = self.store.db.execute("SELECT response FROM turns WHERE session_id=?", (self.session,)).fetchone()
        response = json.loads(row["response"])
        response["outcome"]["proposal"].update(fields)
        with self.store.db:
            self.store.db.execute("UPDATE turns SET response=? WHERE session_id=?", (json.dumps(response), self.session))

    def refresh_source(self):
        commit(self.repository, "Updated acceptance fixture")
        self.session = self.store.create(str(self.repository), "HEAD")["id"]
        with patch.object(ChatOpenRouter, "_generate", scripted_generate):
            dispatch(Request(operation="chat", request_id="proposal", session_id=self.session, query="proposal cap 10 and timeout 20"), self.store)

    def test_baseline_and_protected_oracle_are_bound_to_delivery(self):
        info = self.execute(self.approve())
        self.assertEqual(info["status"], "verified", info["message"])
        self.assertEqual(info["baseline_checks"][0]["outcome"], "failed")
        self.assertEqual(info["checks"][0]["outcome"], "passed")
        self.assertEqual(info["checks"][0]["test_count"], 2)
        evidence = json.loads(Path(info["artifact"]["evidence"]).read_text())
        self.assertIn("test_behavior.py", evidence["contract"]["protected_inputs"])
        self.assertEqual(evidence["checks"][0]["environment"], evidence["contract"]["environment"])
        self.assertIsNone(evidence["usage"]["cost"])

    def test_effective_contract_has_one_check_and_assignment_identity(self):
        self.proposal(checks=[{"id": "draft-check", "argv": ["python3.12", "-c", "pass"]}],
                      work_items=[{"id": "draft-worker", "instruction": "Draft only", "paths": ["reconnect.py"]}])
        result = self.request("contract", execution=self.settings)["contract"]["data"]
        self.assertEqual(result["proposal"]["checks"], result["checks"])
        self.assertEqual(result["proposal"]["work_items"], result["work_items"])
        original = json.loads(self.store.db.execute("SELECT response FROM turns WHERE session_id=?", (self.session,)).fetchone()[0])
        self.assertEqual(original["outcome"]["proposal"]["work_items"][0]["id"], "draft-worker")

    def test_assurance_receives_current_reports_and_records_rejected_coverage(self):
        from execution import execute_run
        handoffs = []
        def missing_coverage(self, messages, **kwargs):
            prompt = "\n".join(str(m.content) for m in messages if m.type == "system")
            result = scripted_execution_generate(self, messages, **kwargs)
            if "independent assurance reviewer" in prompt:
                payload, _ = json.JSONDecoder().raw_decode(prompt[prompt.index('{"contract":'):])
                handoffs.append(payload)
                for call in result.generations[0].message.tool_calls:
                    if call["name"] == "Review":
                        call["args"]["coverage"] = []
            return result
        run_id = self.approve()
        with patch.object(ChatOpenRouter, "_generate", missing_coverage):
            execute_run(self.store.root, run_id)
        info = Runs(self.store).info(run_id)
        self.assertEqual(info["failure_category"], "evidence")
        self.assertEqual({report["item"] for report in handoffs[-1]["worker_reports"]}, {"cap", "timeout"})
        self.assertTrue(all(report["report"] for report in handoffs[-1]["worker_reports"]))
        rejected = [json.loads(row[0]) for row in self.store.db.execute(
            "SELECT data FROM run_events WHERE run_id=? AND kind='assurance_candidate'", (run_id,))]
        self.assertEqual(rejected[-1]["coverage"], [])
        self.assertIn("missing criteria=[0, 1]", info["message"])

    def test_declared_owned_test_cannot_weaken_protected_assertions(self):
        self.proposal(affected_paths=["reconnect.py", "limits.py", "test_behavior.py"])
        self.settings["work_items"].append({"id": "tests", "instruction": "Remove assertions", "paths": ["test_behavior.py"]})
        run_id = self.approve()
        def tamper(context, contract, item, key, workspace, feedback):
            if item.id == "tests":
                (workspace / "test_behavior.py").write_text("import unittest\n")
            return WorkerReport(summary="Candidate")
        with patch("execution.implement", tamper):
            info = self.execute(run_id)
        self.assertEqual(info["status"], "waiting_approval")
        self.assertEqual(info["failure_category"], "evidence")
        self.assertIsNone(info["artifact"])
        self.assertIn("assertEqual", (self.repository / "test_behavior.py").read_text())

    def test_environment_change_rejects_approval_without_a_run(self):
        contract = self.request("contract", execution=self.settings)["contract"]
        original = capture_environment(self.repository, contract["data"]["source_revision"], Runs(self.store).contract(contract["hash"]).checks)
        details = {**original.details, "architecture": "different"}
        changed = original.model_copy(update={"details": details, "fingerprint": digest(details)})
        with patch("profiles.capture_environment", return_value=changed), self.assertRaisesRegex(BoundaryFailure, "environment changed"):
            self.request("approve", contract_hash=contract["hash"])
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM runs").fetchone()[0], 0)

    def test_environment_change_before_dispatch_has_no_model_calls(self):
        run_id = self.approve()
        with patch("profiles.capture_environment", side_effect=BoundaryFailure("environment", "Environment drift", amendment=True)):
            info = self.execute(run_id)
        self.assertEqual(info["status"], "waiting_approval")
        self.assertEqual(info["model_calls"], 0)

    def test_guidance_change_invalidates_approved_dispatch(self):
        run_id = self.approve()
        changed = {**GUIDANCE["bounded-implementation"], "text": "Changed reviewed guidance"}
        with patch.dict(GUIDANCE, {"bounded-implementation": changed}):
            info = self.execute(run_id)
        self.assertEqual(info["status"], "waiting_approval")
        self.assertEqual(info["failure_category"], "policy")
        self.assertEqual(info["model_calls"], 0)

    def test_unreviewed_guidance_and_model_defaults_are_rejected(self):
        for index, fields in enumerate(({"guidance_ids": ["untrusted-skill"]}, {"role_models": {"reviewer": "openrouter/auto"}},
                       {"role_models": {"unbounded_subagent": "test/offline"}})):
            with self.subTest(fields=fields), self.assertRaises(ValueError):
                self.request("contract", identity="invalid-" + str(index), execution={**self.settings, **fields})

    def test_guidance_cannot_gain_capabilities(self):
        changed = {**GUIDANCE["independent-assurance"], "capabilities": ["read", "publish"]}
        with patch.dict(GUIDANCE, {"independent-assurance": changed}), self.assertRaisesRegex(ValueError, "capabilities"):
            self.request("contract", execution=self.settings)

    def test_legacy_records_are_preserved_but_old_approval_cannot_execute(self):
        current = self.request("contract", execution=self.settings)["contract"]
        legacy = copy.deepcopy(current["data"])
        for field in ("schema_version", "environment", "workflow", "protected_inputs", "mode", "task_type", "role_models", "guidance_ids"):
            legacy.pop(field, None)
        legacy["policy_version"] = "local-bwrap-v1"
        identity = digest(legacy)
        with self.store.db:
            self.store.db.execute("UPDATE contracts SET hash=?,data=? WHERE hash=?", (identity, json.dumps(legacy), current["hash"]))
        with self.assertRaisesRegex(BoundaryFailure, "Legacy"):
            self.request("approve", contract_hash=identity)
        self.assertEqual(Runs(self.store).latest(self.session)["data"], legacy)
        replacement = self.request("contract", identity="replacement", execution=self.settings)["contract"]
        self.assertEqual(replacement["data"]["schema_version"], 2)
        self.assertEqual(self.store.db.execute("SELECT data FROM contracts WHERE hash=?", (identity,)).fetchone()[0], json.dumps(legacy))

    def test_empty_and_skipped_suites_never_pass(self):
        for content in ("import unittest\n", "import unittest\n@unittest.skip('disabled')\nclass Check(unittest.TestCase):\n    def test_disabled(self): pass\n"):
            with self.subTest(content=content):
                (self.repository / "test_behavior.py").write_text(content)
                self.refresh_source()
                info = self.execute(self.approve())
                self.assertEqual(info["status"], "failed")
                self.assertEqual(info["failure_category"], "evidence")
                self.assertEqual(info["model_calls"], 0)

    def test_missing_dependency_is_environment_failure_without_repairs(self):
        (self.repository / "test_behavior.py").write_text("import nonexistent_shinobi_dependency\n")
        self.refresh_source()
        info = self.execute(self.approve())
        self.assertEqual(info["status"], "blocked")
        self.assertEqual(info["failure_category"], "environment")
        self.assertEqual(info["repair_cycle"], 0)
        self.assertEqual(info["model_calls"], 0)

    def test_refactor_requires_passing_characterization_before_writes(self):
        self.proposal(task_type="refactor", preserved_behavior=["Retry behavior and timeout remain unchanged"])
        info = self.execute(self.approve())
        self.assertEqual(info["status"], "failed")
        self.assertEqual(info["failure_category"], "code")
        self.assertEqual(info["model_calls"], 0)

    def test_recovery_enforces_previously_recorded_failed_baseline(self):
        from execution import execute_run
        self.proposal(task_type="refactor", preserved_behavior=["Retry behavior and timeout remain unchanged"])
        run_id = self.approve()
        with patch("execution.require_available", side_effect=KeyboardInterrupt("Interrupted after persisting baseline")):
            info = self.execute(run_id)
        self.assertTrue(info["baseline_checks"])
        runs = Runs(self.store)
        with runs.transaction():
            runs.update(run_id, status="queued", launch_requested=True)
        with patch.object(ChatOpenRouter, "_generate", side_effect=AssertionError("Recovery must not dispatch")):
            execute_run(self.store.root, run_id)
        info = runs.info(run_id)
        self.assertEqual(info["failure_category"], "code")
        self.assertEqual(info["model_calls"], 0)

    def test_recovery_rejects_changed_recorded_baseline(self):
        from execution import execute_run
        run_id = self.approve()
        with patch("execution.run_graph", side_effect=KeyboardInterrupt("Interrupted after baseline")):
            info = self.execute(run_id)
        folder = self.store.root / "runs" / run_id
        candidate = folder / "saved-candidate"
        from workspace import artifact_hash, copy_workspace
        copy_workspace(folder / "baseline", candidate)
        (folder / "baseline" / "reconnect.py").write_text("def retry_delay(attempt): return 10\n")
        runs = Runs(self.store)
        with runs.transaction():
            runs.update(run_id, status="queued", launch_requested=True, workspace=str(candidate), workspace_hash=artifact_hash(candidate))
        with patch.object(ChatOpenRouter, "_generate", side_effect=AssertionError("Recovery must not dispatch")):
            execute_run(self.store.root, run_id)
        info = runs.info(run_id)
        self.assertEqual(info["status"], "waiting_approval")
        self.assertEqual(info["failure_category"], "evidence")
        self.assertEqual(info["model_calls"], 0)

    def test_diagnostic_has_no_mutation_tools_and_never_claims_a_fix(self):
        self.proposal(task_type="investigation", affected_paths=[], changed_behavior=[],
                      acceptance_criteria=["Observe the existing failure without changing source"])
        self.settings.update(mode="diagnostic", work_items=[{"id": "diagnose", "instruction": "Read retry behavior", "paths": [], "input_paths": ["reconnect.py"]}])
        self.settings["checks"][0]["expected_exit_code"] = 1
        def diagnose(self, messages, **kwargs):
            from langchain_core.messages import AIMessage, ToolMessage
            from helpers import output
            prompt = "\n".join(str(m.content) for m in messages if m.type == "system")
            if "independent assurance reviewer" in prompt:
                return scripted_execution_generate(self, messages, **kwargs)
            if not any(isinstance(m, ToolMessage) for m in messages):
                return output(AIMessage(content="", tool_calls=[{"name": "read_source", "args": {"path": "reconnect.py"}, "id": "read"}]))
            return output(AIMessage(content="", tool_calls=[{"name": "DiagnosticReport", "args": {
                "summary": "The baseline cap is 30; the approved reproduction exits 1.",
                "observations": ["reconnect.py:2 caps retry_delay at 30; approved behavior reproduction exits 1."],
                "limitations": ["Two tests cover the requested constants; they do not establish every input or integration path."]}, "id": "report"}]))
        run_id = self.approve()
        before = manifest(self.repository)
        with patch.object(ChatOpenRouter, "_generate", diagnose):
            from execution import execute_run
            execute_run(self.store.root, run_id)
        info = Runs(self.store).info(run_id)
        self.assertEqual(info["status"], "verified", info["message"])
        self.assertEqual(info["artifact"]["disposition"], "diagnostic")
        for attempt in info["attempts"].values():
            self.assertFalse({"write_source", "replace_source", "delete_source"} & set(attempt["bound_tools"]))
        self.assertEqual(manifest(self.repository), before)
        self.assertEqual(Path(info["artifact"]["patch"]).read_bytes(), b"")
        from execution_api import summary
        visible = summary(Runs(self.store), run_id)["diagnostic_reports"]
        self.assertIn("30", visible[0]["observations"][0])
        self.assertTrue(visible[0]["limitations"])

    def test_diagnostic_disclaimer_without_findings_cannot_verify(self):
        from execution import execute_run
        from langchain_core.messages import AIMessage
        from helpers import output
        self.proposal(task_type="investigation", affected_paths=[], changed_behavior=[],
                      acceptance_criteria=["Observe cap and check limits without changing source"])
        self.settings.update(mode="diagnostic", work_items=[{"id": "diagnose", "instruction": "Read retry behavior", "paths": []}])
        self.settings["checks"][0]["expected_exit_code"] = 1
        run_id = self.approve()
        before = manifest(self.repository)
        def stub(self, messages, **kwargs):
            return output(AIMessage(content="", tool_calls=[{"name": "DiagnosticReport", "args": {
                "summary": "No files changed", "observations": [], "limitations": []}, "id": "stub"}]))
        with patch.object(ChatOpenRouter, "_generate", stub):
            execute_run(self.store.root, run_id)
        info = Runs(self.store).info(run_id)
        self.assertEqual(info["status"], "failed")
        self.assertEqual(info["failure_category"], "evidence")
        self.assertEqual(info["repair_cycle"], 0)
        self.assertIsNone(info["artifact"])
        self.assertEqual(before, manifest(self.repository))

    def test_read_errors_are_visible_and_recoverable_without_source_access_expansion(self):
        from execution import read_tools
        from sandbox import Sandbox
        reader = next(tool for tool in read_tools(Sandbox(self.repository)) if tool.name == "read_source")
        missing = reader.invoke({"type": "tool_call", "name": "read_source", "id": "missing", "args": {"path": "test_behavior"}})
        self.assertEqual(missing.status, "error")
        valid = reader.invoke({"type": "tool_call", "name": "read_source", "id": "valid", "args": {"path": "test_behavior.py"}})
        self.assertEqual(valid.status, "success")
        self.assertIn("assertEqual", valid.content)
        denied = reader.invoke({"type": "tool_call", "name": "read_source", "id": "denied", "args": {"path": "../outside"}})
        self.assertEqual(denied.status, "error")

    def test_producer_consumer_requires_dependency_and_records_input_identity(self):
        self.settings["work_items"][1]["input_paths"] = ["reconnect.py"]
        with self.assertRaisesRegex(ValueError, "producer/consumer"):
            self.request("contract", execution=self.settings)
        self.settings["work_items"][1]["depends_on"] = ["cap"]
        info = self.execute(self.approve())
        self.assertEqual(info["status"], "verified", info["message"])
        consumer = next(value for value in info["attempts"].values() if value["item"] == "timeout")
        self.assertEqual(consumer["input_manifest"]["reconnect.py"][0], manifest(Path(info["artifact"]["workspace"]))["reconnect.py"][0])

    def test_disjoint_writes_sharing_an_interface_are_serialized(self):
        for item in self.settings["work_items"]:
            item["interfaces"] = ["retry-policy"]
        info = self.execute(self.approve())
        self.assertEqual(info["status"], "verified", info["message"])
        batches = [json.loads(event["data"])["items"] for event in self.store.db.execute(
            "SELECT data FROM run_events WHERE run_id=? AND kind='scheduled'", (info["id"],))]
        self.assertEqual(batches, [["cap"], ["timeout"]])

    def test_provider_errors_do_not_consume_code_repairs(self):
        run_id = self.approve()
        with patch.object(ChatOpenRouter, "_generate", side_effect=RuntimeError("Provider unavailable")):
            from execution import execute_run
            execute_run(self.store.root, run_id)
        info = Runs(self.store).info(run_id)
        self.assertEqual(info["failure_category"], "provider")
        self.assertEqual(info["repair_cycle"], 0)
        self.assertIsNone(info["artifact"])

    def test_invalid_structured_report_is_evidence_failure_without_repairs(self):
        from langchain.agents.structured_output import StructuredOutputError
        from execution import execute_run
        run_id = self.approve()
        with patch.object(ChatOpenRouter, "_generate", side_effect=StructuredOutputError("Malformed report")):
            execute_run(self.store.root, run_id)
        info = Runs(self.store).info(run_id)
        self.assertEqual(info["failure_category"], "evidence")
        self.assertEqual(info["repair_cycle"], 0)
        self.assertIsNone(info["artifact"])

    def test_graph_exhaustion_is_budget_failure_without_repairs(self):
        from langgraph.errors import GraphRecursionError
        from execution import execute_run
        run_id = self.approve()
        with patch.object(ChatOpenRouter, "_generate", side_effect=GraphRecursionError("Graph allowance exhausted")):
            execute_run(self.store.root, run_id)
        info = Runs(self.store).info(run_id)
        self.assertEqual(info["failure_category"], "budget")
        self.assertEqual(info["repair_cycle"], 0)
        self.assertIsNone(info["artifact"])

    def test_noop_requires_explicit_independent_already_satisfied_disposition(self):
        (self.repository / "reconnect.py").write_text("def retry_delay(attempt):\n    return min(2 ** attempt, 10)\n")
        (self.repository / "limits.py").write_text("TIMEOUT = 20\n")
        self.refresh_source()
        run_id = self.approve()
        info = self.execute(run_id)
        self.assertEqual(info["status"], "failed")
        self.assertEqual(info["failure_category"], "evidence")
        self.assertIsNone(info["artifact"])

    def test_explicit_already_satisfied_result_has_a_zero_patch(self):
        (self.repository / "reconnect.py").write_text("def retry_delay(attempt):\n    return min(2 ** attempt, 10)\n")
        (self.repository / "limits.py").write_text("TIMEOUT = 20\n")
        self.refresh_source()
        def already_satisfied(self, messages, **kwargs):
            result = scripted_execution_generate(self, messages, **kwargs)
            for call in result.generations[0].message.tool_calls:
                if call["name"] == "Review":
                    call["args"]["already_satisfied"] = True
                    call["args"]["summary"] = "Source already caps retry at 10 and timeout at 20; the unchanged protected reproduction passes."
            return result
        run_id = self.approve()
        with patch.object(ChatOpenRouter, "_generate", already_satisfied):
            from execution import execute_run
            execute_run(self.store.root, run_id)
        info = Runs(self.store).info(run_id)
        self.assertEqual(info["status"], "verified", info["message"])
        self.assertEqual(info["artifact"]["disposition"], "already_satisfied")
        self.assertEqual(Path(info["artifact"]["patch"]).read_bytes(), b"")
