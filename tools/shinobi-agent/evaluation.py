"""Compare versioned local workflow trials without changing runtime defaults."""
import json
from pathlib import Path
import statistics

from execution_contracts import digest


def load_corpus(path):
    corpus = json.loads(Path(path).read_text())
    cases = corpus["cases"]
    if corpus["version"] != 1 or len({case["id"] for case in cases}) != len(cases):
        raise ValueError("Unsupported corpus or duplicate case identity")
    if {case["task_type"] for case in cases} != {"investigation", "bug_fix", "feature", "refactor"}:
        raise ValueError("Corpus must cover all four supported processes")
    if not any(case["split"] == "held_out" for case in cases):
        raise ValueError("A held-out split is required")
    return corpus, digest(corpus)


def summarize(records):
    durations = [record["seconds"] for record in records]
    correct = sum(record["status"] == "verified" and record["independently_correct"] for record in records)
    known_cost = all(record.get("cost") is not None for record in records)
    return {"samples": len(records), "correct_completions": correct,
            "correct_completion_rate": correct / len(records),
            "false_successes": sum(record["status"] == "verified" and not record["independently_correct"] for record in records),
            "unauthorized_actions": sum(not record["source_unchanged"] or bool(record["scope_violations"]) for record in records),
            "median_seconds": statistics.median(durations),
            "seconds_stdev": statistics.stdev(durations) if len(durations) > 1 else None,
            "total_model_calls": sum(record["model_calls"] for record in records),
            "total_repairs": sum(record["repair_cycles"] for record in records),
            "total_cost": sum(record["cost"] for record in records) if known_cost else None,
            "cost_per_correct_completion": sum(record["cost"] for record in records) / correct if known_cost and correct else None,
            "human_interventions": sum(record["human_interventions"] for record in records)
                if all(record.get("human_interventions") is not None for record in records) else None,
            "failures": [{"case": record["case"], "category": record.get("failure_category"), "message": record.get("message")}
                         for record in records if record["status"] != "verified"]}


def compare(corpus, records, configurations):
    if not records:
        raise ValueError("No evaluation evidence")
    identities = [(record["configuration"], record["case"], record["repeat"]) for record in records]
    if len(identities) != len(set(identities)):
        raise ValueError("Duplicate trial identity cannot count as another sample")
    expected = {case["id"] for case in corpus["cases"]}
    if any(record["case"] not in expected or record["configuration"] not in configurations for record in records):
        raise ValueError("Evidence references an unknown case or configuration")
    summaries = {}
    for name in configurations:
        selected = [record for record in records if record["configuration"] == name]
        if not selected:
            raise ValueError("A configuration has no trials")
        summaries[name] = {**summarize(selected), "cases": {
            case: summarize([record for record in selected if record["case"] == case])
            for case in sorted(expected) if any(record["case"] == case for record in selected)}}
    baseline = next((name for name, config in configurations.items() if config["workers"] == 1), None)
    decisions = {}
    for name, summary in summaries.items():
        if name == baseline:
            continue
        selected = [record for record in records if record["configuration"] == name]
        reasons = []
        if any(record["generation"] != "live" for record in records):
            reasons.append("Scripted generation establishes controller behavior, not model quality or a production improvement")
        for config in (name, baseline):
            rows = [record for record in records if record["configuration"] == config]
            if not rows or any(len({row["repeat"] for row in rows if row["case"] == case}) < corpus["thresholds"]["minimum_repeats"] for case in expected):
                reasons.append("Incomplete repeated baseline or candidate coverage, including held-out tasks")
        if summary["false_successes"] or summary["unauthorized_actions"]:
            reasons.append("A false success or unauthorized action was observed")
        if baseline and (summaries[baseline]["false_successes"] or summaries[baseline]["unauthorized_actions"]):
            reasons.append("The sequential baseline did not satisfy its safety gates")
        if baseline is None or summary["correct_completion_rate"] < summaries[baseline]["correct_completion_rate"]:
            reasons.append("Correct completion did not meet the sequential baseline")
        if any(row["status"] != "verified" for row in selected):
            reasons.append("At least one required task did not complete")
        if baseline:
            faster = summary["median_seconds"] <= summaries[baseline]["median_seconds"] * (1 - corpus["thresholds"]["minimum_improvement_fraction"])
            base_cost, candidate_cost = summaries[baseline]["cost_per_correct_completion"], summary["cost_per_correct_completion"]
            cheaper = base_cost is not None and candidate_cost is not None and candidate_cost <= base_cost * (1 - corpus["thresholds"]["minimum_improvement_fraction"])
            if not faster and not cheaper:
                reasons.append("No predeclared improvement in time or known cost was observed")
        decisions[name] = {"eligible_for_review": not reasons, "reasons": reasons,
                           "automatic_adoption": False}
    return {"corpus_version": corpus["version"], "corpus_hash": digest(corpus), "thresholds": corpus["thresholds"],
            "configurations": configurations, "baseline": baseline, "summaries": summaries, "decisions": decisions,
            "limitations": ["Small stdlib fixture corpus; not evidence of broad repository quality",
                            "Live trials require separately configured models; unknown cost and human effort remain unknown",
                            "Measured variability is descriptive; no statistical confidence or automatic policy change is asserted"]}
