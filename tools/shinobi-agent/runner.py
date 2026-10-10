"""One protocol request per process; completed conversations outlive both Pi and Python."""

import contextlib
import json
import os
from pathlib import Path
import signal
import sys

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langchain_core.messages import ToolMessage

from agent import Evidence, configuration, make_agent, sanitize
from contracts import Outcome, Request
from repository import validate_evidence
from store import Store

MAX_REQUEST_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 256 * 1024
TIMEOUT_SECONDS = 120


class Interrupted(Exception):
    pass


def interrupt(signum, frame):
    raise Interrupted("Turn interrupted or timed out. It was not completed or automatically replayed.")


def session_summary(store, session_id):
    session = store.info(session_id)
    session.pop("history")
    session["excluded_count"] = len(session["excluded"])
    session["excluded"] = session["excluded"][:50]
    return session


def dispatch(request: Request, store: Store):
    if request.operation == "create":
        session = store.create(request.repository, request.revision)
        return {"session": session_summary(store, session["id"])}
    if request.operation == "list":
        return {"sessions": [{k: s[k] for k in ("id", "repository", "revision", "created_at")} for s in store.list()]}
    if request.operation not in {"chat", "resume"}:
        from execution_api import dispatch_execution
        return {**dispatch_execution(request, store), "session": session_summary(store, request.session_id)}
    with store.locked(request.session_id):
        if request.operation == "resume":
            session = store.info(request.session_id)
            history = session["history"][-5:]
            for turn in history:
                turn["query"] = turn["query"][:2000]
                response = turn["response"] or {}
                turn["response"] = {"message": response.get("outcome", response).get("message", "")[:8000]}
            return {"session": session_summary(store, request.session_id), "history": history}
        previous = store.previous(request.session_id, request.request_id, request.query)
        if previous:
            if previous["status"] == "completed":
                return {**json.loads(previous["response"]), "replayed": True}
            raise ValueError(f"Request already {previous['status']}; it will not be replayed. Submit a new turn explicitly.")
        from execution_api import steer_before_chat
        steer_before_chat(store, request.session_id, request.query)
        store.begin(request.session_id, request.request_id, request.query)
        try:
            model_id = configuration()
            row = store.row(request.session_id)
            metadata = json.loads(row["metadata"])
            reads = json.loads(row["reads"])
            evidence = Evidence()
            with SqliteSaver.from_conn_string(str(store.root / "checkpoints.sqlite")) as saver:
                saver.serde = JsonPlusSerializer(allowed_msgpack_modules=[
                    ("contracts", "Outcome"), ("contracts", "Proposal"), ("contracts", "Citation"),
                ])
                agent = make_agent(model_id, store.workspace(request.session_id), metadata, reads, saver)
                prior = {}
                if row["checkpoint"]:
                    prior = agent.get_state(json.loads(row["checkpoint"])).values
                messages = list(prior.get("messages", []))
                # Each attempted turn has its own checkpoint thread. Only a completed turn
                # advances the session pointer; failed model/tool messages cannot leak forward.
                config = {"configurable": {"thread_id": request.session_id + ":" + request.request_id},
                          "recursion_limit": 30, "callbacks": [evidence]}
                directions = [r["instruction"] for r in store.db.execute(
                    "SELECT instruction FROM session_directions WHERE session_id=? AND proposal_version>=? ORDER BY seq",
                    (request.session_id, row["proposal_version"]))]
                query = ("Saved user steering instructions (newest last):\n" + "\n".join(directions) + "\nCurrent request:\n" if directions else "") + request.query
                inputs = {"messages": messages + [{"role": "user", "content": query}],
                          "files": prior.get("files", {})}
                result = agent.invoke(inputs, config=config)
                for message in result["messages"][len(messages) + 1:]:
                    if isinstance(message, ToolMessage) and message.status == "error" and not any(
                        c["name"] == message.name and c["status"] == "error" for c in evidence.calls
                    ):
                        evidence.calls.append({"name": message.name, "status": "error", "blocked_before_execution": True})
                outcome = Outcome.model_validate(result.get("structured_response"))
                validate_evidence(outcome, store.workspace(request.session_id), reads)
                checkpoint = agent.get_state(config).config
            response = {"outcome": outcome.model_dump(), "model": model_id,
                        "tool_calls": evidence.calls, "model_calls": evidence.models,
                        "bound_tools": sorted(evidence.bound_tools),
                        "session": session_summary(store, request.session_id)}
            # Redact before persisting/displaying output. Do not alter the user's stored input.
            response = json.loads(sanitize(json.dumps(response)))
            if len(json.dumps(response).encode()) > MAX_RESPONSE_BYTES - 2048:
                raise ValueError("Response exceeds the transport limit; turn was not completed")
            store.complete(request.session_id, request.request_id, response, checkpoint, reads)
            return response
        except Exception as exc:
            store.fail(request.session_id, request.request_id, sanitize(str(exc))[:1000],
                       "interrupted" if isinstance(exc, Interrupted) else "failed")
            raise


def main():
    os.umask(0o077)
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    signal.signal(signal.SIGALRM, interrupt)
    signal.signal(signal.SIGTERM, interrupt)
    signal.alarm(TIMEOUT_SECONDS)
    request_id = "unknown"
    try:
        data = sys.stdin.buffer.read(MAX_REQUEST_BYTES + 1)
        if len(data) > MAX_REQUEST_BYTES:
            raise ValueError("Request exceeds 64 KiB")
        raw = json.loads(data)
        if isinstance(raw, dict) and isinstance(raw.get("request_id"), str):
            request_id = raw["request_id"][:128]
        request = Request.model_validate(raw)
        root = Path(os.environ.get("SHINOBI_STATE_DIR", str(Path(__file__).parent / ".state")))
        store = Store(root)
        try:
            with contextlib.redirect_stdout(sys.stderr):
                response = dispatch(request, store)
        finally:
            store.close()
        response.update(version=1, request_id=request_id, status="ok")
    except Exception as exc:
        # Pydantic errors can echo input; expose only a concise summary for validation.
        from pydantic import ValidationError
        detail = "Invalid request or agent response schema" if isinstance(exc, ValidationError) else str(exc)
        response = {"version": 1, "request_id": request_id, "status": "error", "error": sanitize(detail)[:1000]}
    finally:
        signal.alarm(0)
    encoded = json.dumps(response, ensure_ascii=False) + "\n"
    if len(encoded.encode()) > MAX_RESPONSE_BYTES:
        response = {"version": 1, "request_id": request_id, "status": "error", "error": "Response too large; inspect the session with resume"}
        encoded = json.dumps(response) + "\n"
    sys.stdout.write(encoded)
    return 0 if response["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
