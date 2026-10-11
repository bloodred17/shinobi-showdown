"""Script only model responses; real controller, tools, graph and sandbox remain active."""
import json
from langchain_core.messages import AIMessage, ToolMessage

from helpers import output


def scripted_execution_generate(self, messages, **kwargs):
    from lifecycle_helpers import stage_generate
    stage = stage_generate(messages)
    if stage is not None:
        return stage
    prompt = "\n".join(str(m.content) for m in messages if m.type == "system")
    if "independent assurance reviewer" in prompt:
        if not any(isinstance(m, ToolMessage) and m.name == "read_source" for m in messages):
            return output(AIMessage(content="", tool_calls=[{"name": "read_source", "args": {"path": "reconnect.py"}, "id": "review-read"}]))
        # Coverage count comes from the actual supplied immutable contract.
        start = prompt.index('{"contract":')
        payload, _ = json.JSONDecoder().raw_decode(prompt[start:])
        checks = [c["id"] for c in payload["contract"]["checks"]]
        coverage = [{"criterion": i, "check_ids": checks, "explanation": "The independent behavior assertions pass for this artifact."}
                    for i, _ in enumerate(payload["contract"]["proposal"]["acceptance_criteria"])]
        return output(AIMessage(content="", tool_calls=[{"name": "Review", "args": {
            "verdict": "pass", "summary": "Behavior and scope verified", "findings": [], "coverage": coverage}, "id": "review"}]))
    start = prompt.index('{"contract":')
    payload, _ = json.JSONDecoder().raw_decode(prompt[start:])
    item = payload["assignment"]
    path = item["paths"][0]
    calls = [m.name for m in messages if isinstance(m, ToolMessage)]
    if "read_source" not in calls:
        return output(AIMessage(content="", tool_calls=[{"name": "read_source", "args": {"path": path}, "id": "worker-read"}]))
    desired = "min(2 ** attempt, 10)" if path == "reconnect.py" else "TIMEOUT = 20"
    already_done = any(isinstance(m, ToolMessage) and m.name == "read_source" and desired in str(m.content) for m in messages)
    if "replace_source" not in calls and not already_done:
        return output(AIMessage(content="", tool_calls=[{"name": "replace_source", "args": {
            "path": path, "old": "30" if path == "reconnect.py" else "60", "new": "10" if path == "reconnect.py" else "20"}, "id": "worker-edit"}]))
    return output(AIMessage(content="", tool_calls=[{"name": "WorkerReport", "args": {
        "summary": "Updated owned behavior", "needs_amendment": False, "reason": ""}, "id": "worker-report"}]))
