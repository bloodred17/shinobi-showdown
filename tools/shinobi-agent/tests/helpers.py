import json
from pathlib import Path
import subprocess

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult


def fixture(root: Path):
    root.mkdir(parents=True)
    def git(*args):
        return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True).stdout
    git("init", "-q")
    (root / "reconnect.py").write_text("def retry_delay(attempt):\n    return min(2 ** attempt, 30)\n")
    (root / "AGENTS.md").write_text("Preserve public function signatures. Propose tests for behavior changes.\n")
    git("add", ".")
    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture")
    return git("rev-parse", "HEAD").decode().strip()


def answer(message="answer", kind="answer", evidence=None, proposal=None, questions=None):
    return {"kind": kind, "message": message, "questions": questions or [], "evidence": evidence or [], "proposal": proposal}


def output(message):
    return ChatResult(generations=[ChatGeneration(message=message)])


def structured(value):
    return output(AIMessage(content="", tool_calls=[{"name": "Outcome", "args": value, "id": "outcome"}]))


def scripted_generate(self, messages, **kwargs):
    """Test-only model replacement. All graph, tools, checkpoints and transport remain real."""
    from lifecycle_helpers import stage_generate
    stage = stage_generate(messages)
    if stage is not None:
        return stage
    users = [m.content for m in messages if isinstance(m, HumanMessage)]
    current = users[-1]
    wants_proposal = "proposal" in current.lower() and "without a new proposal" not in current.lower()
    if current == "FAIL":
        raise RuntimeError("intentional offline model failure")
    if current == "HANG":
        import time
        time.sleep(300)
    if isinstance(messages[-1], HumanMessage) and (wants_proposal or "write" in current.lower()):
        if "write" in current.lower():
            return output(AIMessage(content="", tool_calls=[{"name": "write_file", "args": {"file_path": "/repo/reconnect.py", "content": "changed"}, "id": "forbidden"}]))
        reads = [{"name": "read_file", "args": {"file_path": "/repo/reconnect.py"}, "id": "read-source"}]
        if "timeout" in current.lower():
            reads.append({"name": "read_file", "args": {"file_path": "/repo/limits.py"}, "id": "read-limits"})
        return output(AIMessage(content="", tool_calls=reads))
    if wants_proposal:
        if "timeout" in current.lower():
            return structured(answer("Draft delay and timeout caps", "proposal",
                [{"path": "reconnect.py", "start_line": 1, "end_line": 2, "claim": "The delay cap is 30."},
                 {"path": "limits.py", "start_line": 1, "end_line": 1, "claim": "The timeout is 60."}],
                {"task_type": "bug_fix", "changed_behavior": ["Delay caps at 10; timeout is 20"], "preserved_behavior": ["Public API"],
                 "objective": "Cap delay at 10 and timeout at 20", "constraints": ["Preserve public API"],
                 "exclusions": ["Dependencies and publication"], "approach": ["Change the two constants"],
                 "affected_paths": ["reconnect.py", "limits.py"], "acceptance_criteria": ["Delay caps at 10", "Timeout is 20"],
                 "unresolved_questions": []}))
        cap = "20" if "20" in current else "10"
        return structured(answer(
            "Draft retry cap " + cap, "proposal",
            [{"path": "reconnect.py", "start_line": 1, "end_line": 2, "claim": "The current cap is 30."}],
            {"task_type": "bug_fix", "changed_behavior": ["Retry cap " + cap], "preserved_behavior": ["Public API"],
             "objective": "Change retry cap to " + cap, "constraints": ["Preserve API", "Cap " + cap],
             "exclusions": ["API changes"], "approach": ["Change the cap"], "affected_paths": ["reconnect.py"],
             "acceptance_criteria": ["Delay never exceeds " + cap], "unresolved_questions": []},
        ))
    if "clarify" in current.lower():
        return structured(answer("Which failures should retry?", "needs_input", questions=["Which failures should retry?"]))
    if "write" in current.lower():
        return structured(answer("Repository writes are blocked. I can only propose changes."))
    return structured(answer("Conversation: " + json.dumps(users)))
