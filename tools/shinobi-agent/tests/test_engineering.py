"""Engineering evidence and opt-in autonomy preserve exact-contract authority."""
import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from langchain_core.messages import AIMessage, HumanMessage
from langchain_openrouter import ChatOpenRouter

import test_execution
from contracts import Request
from execution import execute_run
from execution_contracts import Check, WorkerReport
from execution_helpers import scripted_execution_generate
from execution_store import Runs
from helpers import answer, output, scripted_generate, structured
from runner import dispatch
from verification import measure_output
from workflows import skill_record


class EngineeringTests(unittest.TestCase):
    setUp = test_execution.ExecutionTests.setUp
    tearDown = test_execution.ExecutionTests.tearDown
    request = test_execution.ExecutionTests.request
    approve = test_execution.ExecutionTests.approve
    execute = test_execution.ExecutionTests.execute

    def engineering(self):
        return {"acceptance": [
            {"criterion": 0, "check_ids": ["behavior"], "surface": "retry_delay public API",
             "expected_observation": "Delay caps at 10", "limitations": ["No network interaction is tested"]},
            {"criterion": 1, "check_ids": ["behavior"], "surface": "TIMEOUT public constant",
             "expected_observation": "Timeout is 20"}],
            "quality_constraints": [{"id": "compatibility", "requirement": "Existing behavior checks pass",
                                     "check_ids": ["behavior"]}]}

    def metric(self):
        return {"id": "budget", "argv": ["python3.12", "-B", "-c",
            "import json; from reconnect import retry_delay; print(json.dumps({'delay': retry_delay(100)}))"],
            "measurements": [{"key": "delay", "operator": "le", "threshold": 10, "unit": "seconds"}]}

    def test_skills_mapping_measurements_and_autonomy_survive_full_execution(self):
        self.settings.update(engineering=self.engineering(), autonomy="within_contract")
        self.settings["checks"].append(self.metric())
        info = self.execute(self.approve())
        self.assertEqual(info["status"], "verified", info["message"])
        evidence = json.loads(Path(info["artifact"]["evidence"]).read_text())
        contract = evidence["contract"]
        self.assertEqual(contract["autonomy"], "within_contract")
        self.assertEqual(contract["engineering"], contract["proposal"]["engineering"])
        self.assertIn("project-verification", contract["guidance_ids"])
        before = next(c for c in evidence["baseline_checks"] if c["id"] == "budget")
        after = next(c for c in evidence["checks"] if c["id"] == "budget")
        self.assertEqual(before["measurements"][0]["observed"], 30)
        self.assertEqual(before["outcome"], "threshold_failed")
        self.assertEqual(after["measurements"][0]["observed"], 10)
        self.assertEqual(after["artifact_hash"], info["artifact"]["artifact_hash"])
        self.assertEqual(after["measurements"][0]["outcome"], "passed")

    def test_incomplete_duplicate_and_unknown_acceptance_mappings_are_rejected(self):
        for label in ("missing", "duplicate", "unknown", "blank"):
            plan = self.engineering()
            if label == "missing":
                plan["acceptance"].pop()
            elif label == "duplicate":
                plan["acceptance"][1]["criterion"] = 0
            elif label == "unknown":
                plan["acceptance"][0]["check_ids"] = ["not-approved"]
            else:
                plan["acceptance"][0]["expected_observation"] = " "
            with self.subTest(label=label), self.assertRaises(ValueError):
                self.request("contract", identity=label, execution={**self.settings, "engineering": plan})
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM contracts").fetchone()[0], 0)

    def test_quality_constraints_cannot_reference_missing_checks(self):
        plan = self.engineering()
        plan["quality_constraints"][0]["check_ids"] = ["imagined-security-scan"]
        with self.assertRaisesRegex(ValueError, "unknown or duplicate"):
            self.request("contract", execution={**self.settings, "engineering": plan})

    def test_selected_skill_requires_executable_mapping_and_known_identity(self):
        with self.assertRaisesRegex(ValueError, "acceptance-to-check"):
            self.request("contract", execution={**self.settings, "guidance_ids": ["project-verification"]})
        for identity in ("../../AGENTS.md", "pstack", "never-block-on-the-human"):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                skill_record(identity)

    def test_changed_skill_blocks_an_approved_run_before_model_execution(self):
        self.settings["engineering"] = self.engineering()
        run_id = self.approve()
        original = skill_record
        with patch("workflows.skill_record", side_effect=lambda key: {**original(key), "text": "changed guidance"}):
            info = self.execute(run_id)
        self.assertEqual(info["status"], "waiting_approval")
        self.assertEqual(info["model_calls"], 0)

    def test_reviewer_cannot_substitute_checks_for_predeclared_acceptance(self):
        self.settings["engineering"] = self.engineering()
        self.settings["engineering"]["acceptance"][0]["check_ids"].append("budget")
        self.settings["checks"].append(self.metric())
        def omit_mapped_check(model, messages, **kwargs):
            result = scripted_execution_generate(model, messages, **kwargs)
            for call in result.generations[0].message.tool_calls:
                if call["name"] == "Review":
                    call["args"]["coverage"][0]["check_ids"] = ["behavior"]
            return result
        run_id = self.approve()
        with patch.object(ChatOpenRouter, "_generate", omit_mapped_check):
            execute_run(self.store.root, run_id)
        info = Runs(self.store).info(run_id)
        self.assertEqual(info["failure_category"], "evidence")
        self.assertIn("predeclared acceptance", info["message"])
        self.assertIsNone(info["artifact"])

    def test_coordinator_plan_and_selection_reach_contract_without_enabling_autonomy(self):
        settings, plan = self.settings, self.engineering()
        def propose(model, messages, **kwargs):
            result = scripted_generate(model, messages, **kwargs)
            for call in result.generations[0].message.tool_calls:
                if call["name"] == "Outcome" and call["args"].get("proposal"):
                    call["args"]["proposal"].update(checks=settings["checks"], work_items=settings["work_items"],
                        engineering=plan, guidance_ids=["bounded-implementation", "independent-assurance", "project-verification"],
                        guidance_reason="Reuse existing public behavior checks")
                    from lifecycle_helpers import plan_for
                    call["args"]["proposal"]["lifecycle"] = plan_for(call["args"]["proposal"], {**settings, "engineering": plan}, "engineering-proposal", "proposal cap 10 and timeout 20")
                    call["args"]["autonomy_offer"] = "The behavior and checks are bounded"
            return result
        with patch.object(ChatOpenRouter, "_generate", propose):
            result = dispatch(Request(operation="chat", request_id="engineering-proposal", session_id=self.session,
                query="proposal cap 10 and timeout 20"), self.store)
            dispatch(Request(operation="chat", request_id="read-checkpoint", session_id=self.session,
                query="Recall the proposed requirements"), self.store)
        contract = self.request("contract")["contract"]["data"]
        self.assertEqual(contract["engineering"], result["outcome"]["proposal"]["engineering"])
        self.assertTrue(set(result["outcome"]["proposal"]["guidance_ids"]) <= set(contract["guidance_ids"]))
        self.assertEqual(contract["autonomy"], "standard")
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM runs").fetchone()[0], 0)

    def test_autonomy_only_drafts_and_requires_the_new_exact_hash(self):
        self.settings["engineering"] = self.engineering()
        initial = self.request("contract", execution=self.settings)["contract"]
        selected = self.request("contract", identity="select", autonomy="within_contract")["contract"]
        self.assertNotEqual(initial["hash"], selected["hash"])
        for key in ("checks", "work_items", "limits", "engineering", "role_models"):
            self.assertEqual(initial["data"][key], selected["data"][key])
        self.assertEqual(set(selected["data"]["guidance_ids"]),
                         set(initial["data"]["guidance_ids"]) | {"bounded-autonomy"})
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM approvals").fetchone()[0], 0)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM runs").fetchone()[0], 0)
        with self.assertRaisesRegex(ValueError, "latest contract"):
            self.request("approve", contract_hash=initial["hash"])
        reset = self.request("contract", identity="reset", autonomy="standard")["contract"]
        self.assertEqual(reset["data"]["autonomy"], "standard")
        self.assertNotIn("bounded-autonomy", reset["data"]["guidance_ids"])
        self.assertNotEqual(reset["hash"], selected["hash"])
        with self.assertRaisesRegex(ValueError, "latest contract"):
            self.request("approve", identity="stale-selection", contract_hash=selected["hash"])

    def test_autonomy_does_not_apply_to_active_runs_or_waive_amendments(self):
        self.settings["autonomy"] = "within_contract"
        run_id = self.approve()
        with self.assertRaisesRegex(ValueError, "current run"):
            self.request("contract", identity="toggle-active", autonomy="standard")
        with patch("execution.implement", return_value=WorkerReport(summary="Needs a product decision",
                needs_amendment=True, reason="Requested API shape is unresolved")):
            info = self.execute(run_id)
        self.assertEqual(info["status"], "waiting_approval")
        self.assertIsNone(info["artifact"])

    def test_offer_and_skill_read_are_readonly_and_do_not_select_autonomy(self):
        def offer(_self, messages, **_kwargs):
            if isinstance(messages[-1], HumanMessage):
                return output(AIMessage(content="", tool_calls=[{"name": "read_engineering_skill",
                    "args": {"skill_id": "requirements-to-acceptance"}, "id": "read-skill"}]))
            return structured({**answer("Autonomy is optional."), "autonomy_offer": "The task has bounded paths and observable checks."})
        with patch.object(ChatOpenRouter, "_generate", offer):
            result = dispatch(Request(operation="chat", request_id="offer", session_id=self.session,
                query="Could I opt into autonomy?"), self.store)
        self.assertTrue(result["outcome"]["autonomy_offer"])
        self.assertTrue(any(c["name"] == "read_engineering_skill" and c["status"] == "ok" for c in result["tool_calls"]))
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM approvals").fetchone()[0], 0)
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM contracts").fetchone()[0], 0)

    def test_measurements_fail_on_missing_ambiguous_or_non_numeric_evidence(self):
        check = Check.model_validate(self.metric())
        for raw in ('{}', '{"delay":true}', '{"delay":"10"}', '{"delay":NaN}', '{"delay":Infinity}',
                    '{"delay":1e999}', '{"delay":10,"delay":30}', 'logs\n{"delay":10}', '[]'):
            with self.subTest(raw=raw):
                rows, failure = measure_output(check, raw)
                self.assertEqual(failure, "evidence")
                self.assertIsNone(rows[0]["observed"])
        self.assertEqual(measure_output(check, '{"delay":11}')[1], "code")
        self.assertIsNone(measure_output(check, '{"delay":10}')[1])
        for value in (True, "10", float("nan"), float("inf")):
            data = copy.deepcopy(self.metric())
            data["measurements"][0]["threshold"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                Check.model_validate(data)

    def test_zero_exit_with_missing_measurement_blocks_without_repairs(self):
        metric = self.metric()
        metric["argv"][-1] = "print('{}')"
        self.settings["checks"].append(metric)
        info = self.execute(self.approve())
        self.assertEqual(info["failure_category"], "evidence")
        self.assertEqual(info["model_calls"], 0)
        self.assertEqual(info["repair_cycle"], 0)
        self.assertIsNone(info["artifact"])

    def test_numeric_budget_failure_cannot_be_waived_by_reviewer(self):
        metric = self.metric()
        metric["measurements"][0]["threshold"] = 9
        self.settings["checks"].append(metric)
        self.settings["limits"]["repair_cycles"] = 0
        info = self.execute(self.approve())
        self.assertEqual(info["status"], "failed")
        self.assertEqual(info["checks"][-1]["exit_code"], 0)
        self.assertEqual(info["checks"][-1]["outcome"], "threshold_failed")
        self.assertEqual(info["reviews"], [])
        self.assertIsNone(info["artifact"])


if __name__ == "__main__":
    unittest.main()
