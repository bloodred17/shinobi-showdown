"""One request, one real Deep Agent, one scratch directory, one JSON response."""

import contextlib
import json
import os
from pathlib import Path
import re
import signal
import sys
import tempfile
from typing import Any

MAX_REQUEST_BYTES = 64 * 1024
MAX_RESPONSE_BYTES = 256 * 1024
TIMEOUT_SECONDS = 120
RECURSION_LIMIT = 30
FIXTURES = {
    "default": "pear\napple\npear\nbanana\n",
    "changed": "zebra\nkiwi\nzebra\n",
}
SYSTEM_PROMPT = (
    "Complete the user's task directly. Your file tools access a fresh disposable "
    "workspace with /input.txt. For a file task, actually read the requested input, "
    "write the requested output and read it back before answering. Do not include "
    "tool line-number prefixes in written file content. Do not delegate or load "
    "skills or memory. Use only file tools. For a simple question answer directly."
)


class ConfigurationError(ValueError):
    pass


def sanitize(value: str) -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        value = value.replace(key, "[redacted]")
    value = re.sub(r"\bsk-[A-Za-z0-9_-]+", "[redacted]", value)
    return re.sub(r"Bearer\s+[^\s\"']+", "Bearer [redacted]", value, flags=re.I)


def read_request(stream: Any) -> dict[str, str]:
    raw = stream.read(MAX_REQUEST_BYTES + 1)
    if len(raw) > MAX_REQUEST_BYTES:
        raise ConfigurationError("Request exceeds the 64 KiB limit.")
    try:
        request = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise ConfigurationError("Expected one UTF-8 JSON request.") from exc
    if not isinstance(request, dict):
        raise ConfigurationError("Request must be a JSON object.")
    for key in ("request_id", "query"):
        if not isinstance(request.get(key), str) or not request[key].strip():
            raise ConfigurationError(f"Request requires a non-empty {key} string.")
    if len(request["request_id"]) > 128:
        raise ConfigurationError("request_id exceeds 128 characters.")
    return {"request_id": request["request_id"], "query": request["query"]}


def configuration() -> tuple[str, str]:
    model = os.environ.get("SHINOBI_POC_MODEL", "").strip()
    if not model:
        raise ConfigurationError("Set SHINOBI_POC_MODEL to an explicit OpenRouter model ID.")
    # Require a concrete model family. Reject automatic routing and fallback aliases.
    if not re.fullmatch(r"[A-Za-z0-9._-]+/[A-Za-z0-9._:-]+", model):
        raise ConfigurationError("SHINOBI_POC_MODEL must be a vendor/model OpenRouter ID.")
    if model.split("/", 1)[0].lower() in {"openai", "anthropic", "openrouter"}:
        raise ConfigurationError("OpenAI, Anthropic, and automatic routing models are excluded.")
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise ConfigurationError("Set OPENROUTER_API_KEY in the environment.")
    fixture = os.environ.get("SHINOBI_POC_FIXTURE", "default")
    if fixture not in FIXTURES:
        raise ConfigurationError("SHINOBI_POC_FIXTURE must be default or changed.")
    return model, fixture


def make_agent(model_id: str, workspace: Path, callbacks: list[Any] | None = None):
    from deepagents import create_deep_agent
    from deepagents.backends import FilesystemBackend
    from deepagents.profiles import (
        GeneralPurposeSubagentProfile,
        HarnessProfile,
        register_harness_profile,
    )
    from langchain_openrouter import ChatOpenRouter
    from openrouter import OpenRouter

    register_harness_profile(
        f"openrouter:{model_id}",
        HarnessProfile(
            general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
            excluded_tools=frozenset({"write_todos", "execute"}),
        ),
    )
    model = ChatOpenRouter(
        model=model_id,
        base_url="https://openrouter.ai/api/v1",
        # The integration's max_retries=0 leaves SDK retries unset in this pin.
        # Passing retry_config=None explicitly disables the SDK's own backoff.
        client=OpenRouter(
            api_key=os.environ["OPENROUTER_API_KEY"],
            server_url="https://openrouter.ai/api/v1",
            timeout_ms=60_000,
            retry_config=None,
        ),
        max_retries=0,
        timeout=60_000,
        max_tokens=4096,
        openrouter_provider={"require_parameters": True, "allow_fallbacks": False},
        callbacks=callbacks,
    )
    return create_deep_agent(
        model=model,
        backend=FilesystemBackend(root_dir=workspace, virtual_mode=True),
        system_prompt=SYSTEM_PROMPT,
        subagents=[],
        skills=None,
        memory=None,
        checkpointer=None,
    )


def evidence_collector():
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.messages import ToolMessage

    class Evidence(BaseCallbackHandler):
        def __init__(self):
            self.calls: list[dict[str, Any]] = []
            self.by_id: dict[str, dict[str, Any]] = {}
            self.models: list[str] = []
            self.bound_tools: list[str] = []

        def on_chat_model_start(self, serialized, messages, **kwargs):
            parameters = kwargs.get("invocation_params", {})
            self.models.append(parameters.get("model", parameters.get("model_name", "unknown")))
            for tool in parameters.get("tools", []):
                name = tool.get("function", {}).get("name")
                if name and name not in self.bound_tools:
                    self.bound_tools.append(name)

        def on_tool_start(self, serialized, input_str, *, run_id, inputs=None, **kwargs):
            record = {
                "id": str(run_id),
                "name": serialized.get("name", "unknown"),
                "status": "pending",
                "input": sanitize(json.dumps(inputs if inputs is not None else input_str, default=str))[:4096],
            }
            self.calls.append(record)
            self.by_id[str(run_id)] = record

        def on_tool_end(self, output, *, run_id, **kwargs):
            record = self.by_id[str(run_id)]
            text = output.content if isinstance(output, ToolMessage) else str(output)
            text = text if isinstance(text, str) else json.dumps(text, default=str)
            failed = (isinstance(output, ToolMessage) and output.status == "error") or text.lstrip().startswith("Error")
            record.update(status="error" if failed else "ok", output=sanitize(text)[:4096])

        def on_tool_error(self, error, *, run_id, **kwargs):
            self.by_id[str(run_id)].update(status="error", output=sanitize(str(error))[:512])

    return Evidence()


def answer_text(message: Any) -> str:
    content = message.content
    if isinstance(content, str):
        return sanitize(content)
    return sanitize("\n".join(
        block["text"] for block in content
        if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str)
    ))


def deadline(signum, frame):
    raise TimeoutError("Runner timed out; partial scratch work is unverified.")


def main() -> int:
    request_id = "unknown"
    response: dict[str, Any] = {}
    # Prevent ambient LangSmith configuration from exporting this POC's traces.
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(TIMEOUT_SECONDS)
    try:
        request = read_request(sys.stdin.buffer)
        request_id = request["request_id"]
        model_id, fixture = configuration()
        workspace = Path(tempfile.mkdtemp(prefix="shinobi-deepagent-", dir="/tmp"))
        (workspace / "input.txt").write_text(FIXTURES[fixture], encoding="utf-8")
        response.update(model=model_id, workspace=str(workspace), tool_calls=[])
        # Any incidental library prints must not corrupt stdout's JSON contract.
        with contextlib.redirect_stdout(sys.stderr):
            evidence = evidence_collector()
            agent = make_agent(model_id, workspace)
            try:
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": request["query"]}]},
                    config={"recursion_limit": RECURSION_LIMIT, "callbacks": [evidence]},
                )
            finally:
                response.update(tool_calls=evidence.calls, model_calls=evidence.models, bound_tools=evidence.bound_tools)
        answer = answer_text(result["messages"][-1])
        if not answer.strip():
            raise RuntimeError("Agent returned no final text answer.")
        response.update(status="ok", answer=answer)
    except Exception as exc:
        response.update(status="error", error=f"{type(exc).__name__}: {sanitize(str(exc))[:512]}")
    finally:
        signal.alarm(0)
    response["request_id"] = request_id
    encoded = json.dumps(response, ensure_ascii=False) + "\n"
    if len(encoded.encode("utf-8")) > MAX_RESPONSE_BYTES:
        response = {"request_id": request_id, "status": "error", "error": "Response exceeds the 256 KiB limit; partial work is unverified.", "workspace": response.get("workspace")}
        encoded = json.dumps(response) + "\n"
    sys.stdout.write(encoded)
    sys.stdout.flush()
    return 0 if response["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
