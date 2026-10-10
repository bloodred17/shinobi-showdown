"""Small adapter API: only explicit transport operations grant execution approval."""
import json
from pathlib import Path
import subprocess
import sys

from agent import configuration, sanitize
from contracts import Proposal
from execution_contracts import ExecutionSettings, TaskContract
from execution_store import Runs, TERMINAL
from repository import git
from workspace import artifact_hash


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
    value["events"] = [{"seq": e["seq"], "kind": e["kind"], "created_at": e["created_at"]} for e in info["events"]]
    value["checks"] = [{k: c[k] for k in ("id", "exit_code", "artifact_hash", "argv", "cwd")} for c in info["checks"]]
    value["reviews"] = [{"verdict": r["verdict"], "summary": r["summary"], "artifact_hash": r["artifact_hash"]} for r in info["reviews"][-3:]]
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
            settings = ExecutionSettings.model_validate(request.execution or {
                "checks": proposal.checks,
                "work_items": proposal.work_items or [{"id": "implement", "instruction": "\n".join(proposal.approach), "paths": proposal.affected_paths}],
            })
            latest = runs.latest(request.session_id)
            contract = TaskContract(**settings.model_dump(), version=latest["data"]["version"] + 1 if latest else 1,
                                    proposal_version=row["proposal_version"], source_revision=store.info(request.session_id)["revision"],
                                    model=configuration(), proposal=proposal)
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
