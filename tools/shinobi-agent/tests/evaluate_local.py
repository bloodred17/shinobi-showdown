"""Explicit evaluation harness. Scripted generation is test-only; runtime has no fake switch."""
import argparse
from contextlib import nullcontext
import hashlib
import json
import os
from pathlib import Path
import random
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from langchain_core.messages import AIMessage, ToolMessage
from langchain.agents.structured_output import StructuredOutputError
from langgraph.errors import GraphRecursionError
from pydantic import ValidationError
from langchain_openrouter import ChatOpenRouter
from agent import Evidence, configuration, sanitize
from contracts import Request
from evaluation import compare, load_corpus
from execution import execute_run
from execution_contracts import POLICY_VERSION, digest
from execution_store import Runs
from helpers import output
from runner import dispatch
from sandbox import Sandbox
from store import Store
from workflows import GUIDANCE, PLAYBOOKS, SKILLS, skill_record
from workspace import artifact_hash, changes, contains, local_git, manifest


def generation(case):
    def generate(self, messages, **kwargs):
        from lifecycle_helpers import stage_generate
        stage = stage_generate(messages)
        if stage is not None:
            return stage
        prompt = "\n".join(str(message.content) for message in messages if message.type == "system")
        calls = {message.tool_call_id for message in messages if isinstance(message, ToolMessage)}
        def emit(name, arguments, identity):
            return output(AIMessage(content="", tool_calls=[{"name": name, "args": arguments, "id": identity}]))
        if "repository-aware coordinator" in prompt:
            if "discover" not in calls:
                return emit("read_file", {"file_path": "/repo/reconnect.py"}, "discover")
            paths = list(case["targets"])
            proposal = {"task_type": case["task_type"], "objective": case["query"],
                        "changed_behavior": [] if case.get("mode") == "diagnostic" else [item["instruction"] for item in case["items"]],
                        "preserved_behavior": ["The named API and characterized behavior"],
                        "constraints": ["Committed source only; protect existing checks"], "exclusions": ["Dependencies and publication"],
                        "approach": [item["instruction"] for item in case["items"]], "affected_paths": paths,
                        "acceptance_criteria": [item["instruction"] for item in case["items"]], "unresolved_questions": []}
            return emit("Outcome", {"kind": "proposal", "message": "Versioned fixture proposal", "questions": [],
                "evidence": [{"path": "reconnect.py", "start_line": 1, "end_line": 1, "claim": "Inspected the source declaration"}], "proposal": proposal}, "proposal")
        payload, _ = json.JSONDecoder().raw_decode(prompt[prompt.index('{"contract":'):])
        if "independent assurance reviewer" in prompt:
            if "review-read" not in calls:
                return emit("read_source", {"path": "reconnect.py"}, "review-read")
            return emit("Review", {"verdict": "pass", "summary": "Independent protected fixture checks and source inspected", "findings": [],
                "coverage": [{"criterion": index, "check_ids": [check["id"] for check in payload["checks"]],
                              "explanation": "The protected fixture checks establish the assigned criterion"}
                             for index in range(len(payload["contract"]["proposal"]["acceptance_criteria"]))]}, "review")
        item = payload["assignment"]
        for path in item["paths"] or item.get("input_paths", []):
            identity = "read-" + path
            if identity not in calls:
                return emit("read_source", {"path": path}, identity)
        for path in item["paths"]:
            identity = "write-" + path
            if identity not in calls:
                return emit("write_source", {"path": path, "content": case["targets"][path]}, identity)
        if payload["contract"]["mode"] == "diagnostic":
            return emit("DiagnosticReport", {"summary": "The observed retry cap is 30; no fix is authorized.",
                "observations": ["reconnect.py:2 caps retry_delay at 30; the recorded baseline check passed one test."],
                "limitations": ["The single high-attempt assertion does not cover boundary, small, negative, error or integration inputs."]}, "report")
        return emit("WorkerReport", {"summary": "Completed the bounded fixture assignment"}, "report")
    return generate


def trial(case, config, repeat, root, live):
    started = time.monotonic()
    folder = root / (case["id"] + "-" + str(config["workers"]) + "-" + str(repeat))
    repository = folder / "source"
    repository.mkdir(parents=True)
    for name, content in {**case["files"], "AGENTS.md": "Respect owned paths. Preserve the named API. Existing check inputs are protected.\n"}.items():
        path = repository / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    local_git(repository, "init", "-q")
    local_git(repository, "add", ".")
    local_git(repository, "commit", "-qm", "Versioned evaluation source")
    before = manifest(repository)
    store = Store(folder / "state")
    run_id = None
    info = {"status": "failed", "model_calls": 0, "repair_cycle": 0, "usage": {"cost": None}}
    correct, violations, contract = False, [], None
    coordinator_evidence = []
    def meter_coordinator():
        evidence = Evidence()
        coordinator_evidence.append(evidence)
        return evidence
    try:
        session_id = store.create(str(repository), "HEAD")["id"]
        def request(operation, **fields):
            return dispatch(Request(operation=operation, request_id=operation, session_id=session_id, **fields), store)
        settings = {"checks": [{"id": "behavior", "argv": ["python3.12", "-B", "-m", "unittest", "test_behavior"]},
                                *case.get("extra_checks", [])],
                    "work_items": case["items"], "mode": case.get("mode", "implement"),
                    "task_type": case["task_type"], "limits": {"max_workers": config["workers"]},
                    "role_models": config["role_models"]}
        query = case["query"] + "\nThe fixture owner supplies these exact draft execution settings: " + json.dumps(settings) + """
Use these check and assignment IDs. The inline AST assertion, if present, intentionally covers the whole
module; its argv is the chosen structural oracle. No product or oracle decisions remain unresolved.
These settings authorize only a proposal now; execution requires subsequent explicit hash approval.
Return one grounded proposal for this requested process, with no writes during this conversation.
"""
        with patch("runner.Evidence", side_effect=meter_coordinator), (nullcontext() if live else patch.object(ChatOpenRouter, "_generate", generation(case))):
            conversation = request("chat", query=query)
            if conversation["outcome"]["kind"] != "proposal":
                raise ValueError("Proposal was not ready; clarification remains part of the recorded outcome")
            if not live:
                from lifecycle_helpers import plan_for
                settings["lifecycle"] = plan_for(conversation["outcome"]["proposal"], settings, "chat", query)
            planned = request("contract", execution=settings)
            contract = planned["contract"]
            if contract is None:
                raise ValueError("Planning review requires revision: " + json.dumps(planned["planning_review"]))
            run_id = request("approve", contract_hash=contract["hash"])["run"]["id"]
            execute_run(store.root, run_id)
        info = Runs(store).info(run_id)
        if info["status"] == "verified":
            candidate = Path(info["artifact"]["workspace"])
            after = manifest(candidate)
            violations = [name for name in changes(before, after) if not any(contains(scope, name) for scope in contract["data"]["proposal"]["affected_paths"])]
            judge = Sandbox(candidate).execute(["python3.12", "-B", "-c", case["judge"]])
            correct = judge["exit_code"] == 0 and artifact_hash(candidate) == info["artifact"]["artifact_hash"] and not violations
            if case.get("mode") == "diagnostic":
                correct = correct and before == after and info["artifact"]["disposition"] == "diagnostic"
            (folder / "independent-judge.json").write_text(json.dumps(judge, indent=2))
    except Exception as exc:
        info = Runs(store).info(run_id) if run_id else info
        category = ("evidence" if isinstance(exc, StructuredOutputError) else "budget" if isinstance(exc, GraphRecursionError) else
                    "validation" if isinstance(exc, (ValidationError, ValueError)) else "environment" if isinstance(exc, OSError) else "evaluation")
        info = {**info, "message": sanitize(str(exc)), "failure_category": info.get("failure_category") or getattr(exc, "category", category)}
    finally:
        planning_calls = sum(len(json.loads(row['data']).get('model_calls', []))
                             for row in store.db.execute('SELECT data FROM planning_reviews'))
        store.close()
    coordinator_calls = sum(len(evidence.models) for evidence in coordinator_evidence) + planning_calls
    return {"case": case["id"], "split": case["split"], "repeat": repeat, "configuration": config["id"],
            "generation": "live" if live else "scripted", "status": info["status"], "independently_correct": correct,
            "source_unchanged": before == manifest(repository), "scope_violations": violations,
            "seconds": time.monotonic() - started, "model_calls": info["model_calls"] + coordinator_calls, "repair_cycles": info["repair_cycle"],
            "execution_model_calls": info["model_calls"], "coordinator_model_calls": coordinator_calls,
            "cost": None, "usage": {"execution": info.get("usage"), "coordinator": {"model_calls": coordinator_calls, "tokens": None, "cost": None}},
            "human_interventions": None,
            "message": info.get("message"), "failure_category": info.get("failure_category"),
            "contract_hash": contract["hash"] if contract else None,
            "evidence": info.get("artifact", {}).get("evidence") if info.get("artifact") else str(folder / "state"),
            "environment": contract["data"]["environment"]["fingerprint"] if contract else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Use the explicitly configured provider for all model generation")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--workers", default="1,2")
    parser.add_argument("--role-models", type=json.loads, default={})
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--cases", help="Comma-separated case IDs for a recorded targeted acceptance rerun")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    workers = [int(value) for value in args.workers.split(",")]
    if not 1 <= args.repeats <= 20 or not workers or set(workers) - {1, 2} or len(workers) != len(set(workers)):
        parser.error("repeats must be 1-20 and workers must be distinct values from 1,2")
    root = Path(tempfile.mkdtemp(prefix="shinobi-workflow-evaluation-"))
    corpus, corpus_hash = load_corpus(ROOT / "tests/workflow_corpus.json")
    selected_ids = args.cases.split(",") if args.cases else [case["id"] for case in corpus["cases"]]
    if len(selected_ids) != len(set(selected_ids)) or not set(selected_ids) <= {case["id"] for case in corpus["cases"]}:
        parser.error("cases must contain distinct known corpus IDs")
    cases = [case for case in corpus["cases"] if case["id"] in selected_ids]
    configs = {}
    with nullcontext() if args.live else patch.dict(os.environ, {"SHINOBI_MODEL": "test/offline", "OPENROUTER_API_KEY": "offline-test-only"}):
        model = configuration()
        for count in workers:
            config = {"workers": count, "role_models": args.role_models, "model": model,
                      "policy": POLICY_VERSION, "workflow_hash": digest(PLAYBOOKS), "guidance_hash": digest({**GUIDANCE, **{key: skill_record(key) for key in SKILLS}}),
                      "runtime_files": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                        for name in ("agent.py", "runner.py", "execution.py", "execution_api.py", "execution_contracts.py", "engineering.py", "lifecycle.py", "lifecycle_execution.py", "profiles.py", "verification.py", "workflows.py")},
                      "harness_hash": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "selected_cases": selected_ids}
            identity = digest(config)
            configs[identity] = {**config, "id": identity}
        assignments = [(case, config, repeat) for case in cases for config in configs.values() for repeat in range(args.repeats)]
        random.Random(args.seed).shuffle(assignments)
        records = []
        # Evaluation approval is a fixture operation on disposable repositories;
        # no integration can change the user's source or publish externally.
        with patch("execution_api.launch"):
            for case, config, repeat in assignments:
                record = trial(case, config, repeat, root, args.live)
                records.append(record)
                print(json.dumps({key: record[key] for key in ("case", "configuration", "repeat", "status", "independently_correct")}), flush=True)
                (root / "trials.json").write_text(json.dumps(records, indent=2))
    report = {**compare(corpus, records, configs), "source_baseline": local_git(ROOT, "rev-parse", "HEAD").decode().strip(),
              "generation": "live" if args.live else "scripted", "seed": args.seed, "artifact_root": str(root), "records": records}
    target = args.output or root / "evaluation.json"
    target.write_text(sanitize(json.dumps(report, indent=2)))
    print(json.dumps({"report": str(target), "corpus_hash": corpus_hash, "generation": report["generation"],
                      "samples": len(records), "summaries": report["summaries"], "decisions": report["decisions"]}), flush=True)
    return 0 if all(record["independently_correct"] and record["source_unchanged"] and not record["scope_violations"] for record in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
