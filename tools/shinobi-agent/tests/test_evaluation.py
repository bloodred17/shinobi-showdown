import copy
from pathlib import Path
import unittest

from evaluation import compare, load_corpus


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.corpus, self.identity = load_corpus(Path(__file__).with_name("workflow_corpus.json"))
        self.configs = {"sequential": {"workers": 1}, "parallel": {"workers": 2}}
        self.records = [{"configuration": config, "case": case["id"], "repeat": repeat,
                         "generation": "live", "status": "verified", "independently_correct": True,
                         "source_unchanged": True, "scope_violations": [], "seconds": seconds,
                         "model_calls": 10, "repair_cycles": 0, "cost": None, "human_interventions": None}
                        for config, seconds in (("sequential", 10), ("parallel", 5))
                        for case in self.corpus["cases"] for repeat in range(3)]

    def test_unknown_cost_and_human_effort_stay_unknown(self):
        report = compare(self.corpus, self.records, self.configs)
        self.assertIsNone(report["summaries"]["sequential"]["total_cost"])
        self.assertIsNone(report["summaries"]["parallel"]["cost_per_correct_completion"])
        self.assertIsNone(report["summaries"]["parallel"]["human_interventions"])
        self.assertTrue(report["decisions"]["parallel"]["eligible_for_review"])
        self.assertFalse(report["decisions"]["parallel"]["automatic_adoption"])

    def test_scripted_fast_fixture_cannot_authorize_adoption(self):
        for record in self.records:
            record["generation"] = "scripted"
        decision = compare(self.corpus, self.records, self.configs)["decisions"]["parallel"]
        self.assertFalse(decision["eligible_for_review"])
        self.assertTrue(any("Scripted" in reason for reason in decision["reasons"]))

    def test_false_success_and_unauthorized_write_are_not_completion(self):
        wrong = next(record for record in self.records if record["configuration"] == "parallel")
        wrong.update(independently_correct=False, source_unchanged=False)
        report = compare(self.corpus, self.records, self.configs)
        self.assertEqual(report["summaries"]["parallel"]["false_successes"], 1)
        self.assertEqual(report["summaries"]["parallel"]["unauthorized_actions"], 1)
        self.assertFalse(report["decisions"]["parallel"]["eligible_for_review"])

    def test_one_run_and_missing_heldout_evidence_do_not_establish_gain(self):
        records = [record for record in self.records if record["repeat"] == 0 and record["case"] != "coupled-policy"]
        report = compare(self.corpus, records, self.configs)
        self.assertFalse(report["decisions"]["parallel"]["eligible_for_review"])
        self.assertTrue(any("held-out" in reason for reason in report["decisions"]["parallel"]["reasons"]))

    def test_replayed_records_do_not_increase_sample_count(self):
        with self.assertRaisesRegex(ValueError, "Duplicate trial"):
            compare(self.corpus, self.records + [copy.deepcopy(self.records[0])], self.configs)

    def test_failed_attempt_cost_is_included_in_cost_per_completion(self):
        for record in self.records:
            record["cost"] = 1
        failed = next(record for record in self.records if record["configuration"] == "parallel")
        failed.update(status="failed", independently_correct=False)
        report = compare(self.corpus, self.records, self.configs)
        attempts = len(self.corpus["cases"]) * 3
        self.assertEqual(report["summaries"]["parallel"]["cost_per_correct_completion"], attempts / (attempts - 1))
        self.assertFalse(report["decisions"]["parallel"]["eligible_for_review"])
