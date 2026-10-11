"""Small adapter API: only explicit transport operations grant execution approval."""
import json
from pathlib import Path
import subprocess
import sys

from agent import configuration, sanitize
from contracts import Proposal
from execution_contracts import ExecutionSettings, TaskContract, digest, BoundaryFailure
from lifecycle import validate_lifecycle, validate_sources, review_stage
from execution_store import Runs, TERMINAL
from repository import git
from workspace import artifact_hash
from profiles import capture_environment, revalidate_environment
from verification import capture_protection
from workflows import select_workflow, revalidate_workflow


def launch(root, run_id):
    folder = root / "runs" / run_id
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "controller.log").open("ab") as output:
        subprocess.Popen([sys.executable, str(Path(__file__).with_name("execution.py")), str(root), run_id],
                         stdin=subprocess.DEVNULL, stdout=output, stderr=output, start_new_session=True,
                         cwd=Path(__file__).parent)


def summary(runs, run_id):
    if not run_id:
        return None
    info = runs.info(run_id)
    if info["status"] in {"running", "pausing", "cancelling"} and not runs.alive(run_id):
        with runs.transaction():
            latest = runs.info(run_id)
            if latest["status"] in {"running", "pausing", "cancelling"}:
                runs.update(run_id, status="cancelled" if latest["status"] == "cancelling" else "waiting_approval" if latest["invalidated"] else "interrupted",
                            message="Controller stopped; partial artifacts preserved. Explicit recovery required")
                runs.event(run_id, "interrupted", {})
        info = runs.info(run_id)
    if info["status"] == "verified" and artifact_hash(Path(info["workspace"])) != info["artifact"]["artifact_hash"]:
        with runs.transaction():
            runs.update(run_id, status="waiting_approval", invalidated=True, message="Delivered artifact changed; verification is stale")
        info = runs.info(run_id)
    # Keep detailed logs on disk; bound status transport independently of execution history.
    value = {key: info[key] for key in ("id", "session_id", "contract_hash", "status", "message", "repair_cycle", "replans", "model_calls", "completed", "artifact", "invalidated")}
    value.update(failure_category=info.get("failure_category"), baseline_checks=info.get("baseline_checks", []),
                 usage=info.get("usage", {"input_tokens": None, "output_tokens": None, "cost": None}))
    value["events"] = [{"seq": e["seq"], "kind": e["kind"], "created_at": e["created_at"]} for e in info["events"]]
    value["checks"] = [{k: c[k] for k in ("id", "exit_code", "artifact_hash", "argv", "cwd")}
                       | {k: c.get(k) for k in ("outcome", "failure_category", "expected_exit_code", "test_count", "measurements")}
                       for c in info["checks"]]
    value["baseline_checks"] = [{k: c.get(k) for k in ("id", "exit_code", "outcome", "failure_category", "artifact_hash", "test_count")}
                                for c in info.get("baseline_checks", [])]
    value["reviews"] = [{"verdict": r["verdict"], "summary": r["summary"], "artifact_hash": r["artifact_hash"]} for r in info["reviews"][-3:]]
    value["stage_reviews"] = [{k: r[k] for k in ("stage", "verdict", "summary", "artifact_hash", "findings")}
                              for r in info.get("stage_reviews", [])[-4:]]
    if info.get("artifact") and info["artifact"].get("disposition") == "diagnostic":
        reports = {}
        for attempt in info["attempts"].values():
            if attempt.get("status") == "integrated" and attempt.get("report") and attempt["item"] in info["completed"]:
                reports[attempt["item"]] = attempt["report"]
        value["diagnostic_reports"] = [{"item": item, "summary": report["summary"][:1000],
            "observations": [text[:200] for text in report.get("observations", [])[:5]],
            "limitations": [text[:200] for text in report.get("limitations", [])[:5]]}
            for item, report in list(reports.items())[:8]]
    return value


def dispatch_execution(request, store):
    runs = Runs(store)
    saved = runs.replay(request)
    if saved:
        selected = runs.selected(request.session_id, saved.get("run", {}).get("id")) if saved.get("run") else None
        if selected:
            info = runs.info(selected)
            if info["status"] == "queued" and info["launch_requested"]:
                launch(store.root, selected)
        return {**saved, "replayed": True}
    selected = runs.selected(request.session_id, request.run_id)
    # Status observation/reconciliation never holds the adapter transaction across lock probes.
    if request.operation == "status":
        return {"contract": runs.latest(request.session_id), "run": summary(runs, selected)}
    with runs.transaction():
        if runs.replay(request):
            raise ValueError("Concurrent duplicate operation; retry the same request ID")
        if request.operation == "contract":
            if selected and runs.info(selected)["status"] not in TERMINAL:
                raise ValueError("Pause and steer the current run before drafting a replacement contract")
            row = store.row(request.session_id)
            turns = [{"status": "completed", "response": json.loads(r["response"])} for r in
                     store.db.execute("SELECT response FROM turns WHERE session_id=? AND status='completed' ORDER BY rowid", (request.session_id,))]
            proposal_turn = next((t for t in reversed(turns) if t["status"] == "completed" and t["response"].get("proposal_version") == row["proposal_version"]), None)
            if not proposal_turn:
                raise ValueError("Ask for a repository-grounded proposal before creating an executable contract")
            proposal = Proposal.model_validate(proposal_turn["response"]["outcome"]["proposal"])
            latest = runs.latest(request.session_id)
            defaults = {
                "checks": proposal.checks,
                "work_items": proposal.work_items or [{"id": "implement", "instruction": "\n".join(proposal.approach), "paths": proposal.affected_paths}],
                "engineering": proposal.engineering.model_dump() if proposal.engineering else None,
                "lifecycle": proposal.lifecycle.model_dump() if proposal.lifecycle else None,
                "guidance_ids": proposal.guidance_ids,
                "mode": "diagnostic" if proposal.task_type == "investigation" else "implement",
            }
            if request.autonomy is not None and latest:
                if latest["data"]["proposal_version"] != row["proposal_version"]:
                    raise ValueError("Proposal changed; draft its new contract before selecting autonomy")
                # Preserve all reviewed settings when the user changes only the autonomy preference.
                defaults = {key: value for key, value in latest["data"].items() if key in ExecutionSettings.model_fields}
            settings = ExecutionSettings.model_validate({**defaults, **(request.execution or {})})
            if request.autonomy is not None:
                settings.autonomy = request.autonomy
            validate_lifecycle(proposal, settings)
            user_instructions = {r["request_id"]: r["query"] for r in store.db.execute(
                "SELECT request_id,query FROM turns WHERE session_id=? AND status='completed' ORDER BY rowid", (request.session_id,))}
            user_instructions.update({"steer-" + str(r["seq"]): r["instruction"] for r in store.db.execute(
                "SELECT seq,instruction FROM session_directions WHERE session_id=? ORDER BY seq", (request.session_id,))})
            validate_sources(settings.lifecycle, user_instructions)
            metadata = store.info(request.session_id)
            for admission in settings.lifecycle.test_admissions:
                if any((store.workspace(request.session_id) / path).exists() for path in admission.paths):
                    raise ValueError("Test admission requires new paths absent from the committed baseline")
            model = configuration()
            workflow = select_workflow(proposal, settings, model)
            settings.task_type, settings.role_models = workflow.task_type, workflow.models
            settings.guidance_ids = [entry["id"] for entry in workflow.guidance]
            for check in settings.checks:
                if check.baseline_requirement is None:
                    check.baseline_requirement = "pass" if workflow.task_type == "refactor" else "observe"
            protection = capture_protection(metadata["repository"], metadata["revision"], settings.checks)
            environment = capture_environment(metadata["repository"], metadata["revision"], settings.checks)
            # Keep the historical proposal turn intact, but the reviewed executable
            # contract must not carry conflicting draft check/assignment identities.
            proposal = proposal.model_copy(update={"checks": [check.model_dump() for check in settings.checks],
                                                   "work_items": [item.model_dump() for item in settings.work_items],
                                                   "engineering": settings.engineering,
                                                   "lifecycle": settings.lifecycle,
                                                   "guidance_ids": settings.guidance_ids})
            planning_input = {"settings": settings.model_dump(), "proposal": proposal.model_dump(),
                              "source_revision": metadata["revision"], "user_instructions": user_instructions}
            if len(json.dumps(planning_input).encode()) > 120 * 1024:
                raise ValueError("Planning input exceeds the review budget; narrow the task")
            from langchain_core.tools import tool
            from repository import safe_path
            @tool
            def read_source(path: str) -> str:
                """Read committed repository source during independent planning review."""
                source = store.workspace(request.session_id) / safe_path(path)
                if source.is_symlink() or not source.is_file() or source.stat().st_size > 1024 * 1024:
                    raise ValueError("Unavailable source file")
                content = source.read_text()
                return content[:48000] + ("\n[Truncated: narrow the task or source file before relying on complete coverage.]" if len(content) > 48000 else "")
            from workflows import skill_tools
            planning_review = review_stage(workflow.models["reviewer"], "planning",
                {"contract": {**planning_input, **settings.model_dump()}, "workflow": workflow.model_dump()}, [read_source, *skill_tools(workflow)])
            planning_review["input_hash"] = digest(planning_input)
            store.db.execute("INSERT INTO planning_reviews VALUES (?,?,?,?)",
                             (request.session_id, request.request_id, planning_review["input_hash"], json.dumps(planning_review)))
            if planning_review["verdict"] != "pass":
                response = {"contract": None, "planning_review": planning_review}
                runs.remember(request, response)
                return response
            contract = TaskContract(**settings.model_dump(), version=latest["data"]["version"] + 1 if latest else 1,
                                    proposal_version=row["proposal_version"], source_revision=metadata["revision"],
                                    model=model, proposal=proposal, environment=environment,
                                    workflow=workflow, protected_inputs=protection,
                                    planning_review=planning_review, user_instructions=user_instructions)
            if len(json.dumps(contract.model_dump()).encode()) > 192 * 1024:
                raise ValueError("Effective contract exceeds the review transport limit; narrow its check inputs and scope")
            response = {"contract": runs.draft(request.session_id, contract)}
        elif request.operation == "approve":
            latest = runs.latest(request.session_id)
            if not latest or latest["hash"] != request.contract_hash:
                raise ValueError("Approve the exact displayed latest contract hash")
            contract = runs.contract(request.contract_hash)
            repository = store.info(request.session_id)["repository"]
            if git(Path(repository), "rev-parse", "HEAD").decode().strip() != contract.source_revision:
                raise ValueError("Source HEAD changed; create a new session and contract")
            if configuration() != contract.model:
                raise ValueError("Model changed; review a new contract")
            revalidate_environment(contract, repository)
            revalidate_workflow(contract)
            run = runs.new_run(request.session_id, request.contract_hash, request.request_id)
            selected = run["id"]
            response = {"contract": latest, "run": {key: run[key] for key in ("id", "status", "contract_hash", "message")}}
        else:
            if not selected:
                raise ValueError("No run exists in this session")
            run = runs.control(selected, request.operation, sanitize(request.query) if request.query else None)
            response = {"run": {key: run[key] for key in ("id", "status", "contract_hash", "message")}}
        runs.remember(request, response)
    if selected:
        info = runs.info(selected)
        if info["status"] == "queued" and info["launch_requested"]:
            try:
                launch(store.root, selected)
            except OSError:
                with runs.transaction():
                    runs.update(selected, status="interrupted", message="Controller launch failed; use explicit recovery")
                raise
    return response


def steer_before_chat(store, session_id, query):
    runs = Runs(store)
    selected = runs.selected(session_id)
    if selected and runs.info(selected)["status"] not in TERMINAL:
        with runs.transaction():
            runs.control(selected, "steer", sanitize(query))
