"""Immutable authority, bounded work, and deterministic plan validation."""
import hashlib
import json
from pathlib import PurePosixPath
from typing import Literal

from pydantic import Field, model_validator

from contracts import Proposal, StrictModel
from repository import safe_path

POLICY_VERSION = "local-bwrap-v2"


class BoundaryFailure(Exception):
    """A failure whose meaning and recovery policy are known by the controller."""
    def __init__(self, category, message, *, amendment=False):
        super().__init__(message)
        self.category, self.amendment = category, amendment


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def scope_path(value: str) -> str:
    if value.rstrip("/") != safe_path(value) or value in {".", "", "/"} or any(x in value for x in "*?["):
        raise ValueError("Scope must contain explicit relative files or directories ending in /; no glob patterns")
    if any(part in {".git", ".state", "node_modules", ".venv"} for part in PurePosixPath(value).parts):
        raise ValueError("Internal state and dependency trees cannot be writable scope")
    return value


def contains(scope: str, path: str) -> bool:
    return path == scope.rstrip("/") or (scope.endswith("/") and path.startswith(scope))


def overlaps(left: list[str], right: list[str]) -> bool:
    return any(contains(a, b.rstrip("/")) or contains(b, a.rstrip("/")) for a in left for b in right)


class Check(StrictModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    argv: list[str] = Field(min_length=1, max_length=64)
    cwd: str = "."
    timeout_seconds: int = Field(default=60, ge=1, le=120)
    affected_items: list[str] = Field(default_factory=list)
    protected_paths: list[str] | None = None
    expected_exit_code: int = Field(default=0, ge=0, le=255)
    baseline_requirement: Literal["observe", "pass"] | None = None

    @model_validator(mode="after")
    def valid_command(self):
        if any(not arg or "\0" in arg or len(arg) > 8000 for arg in self.argv):
            raise ValueError("Invalid command argument")
        if self.cwd != ".":
            scope_path(self.cwd)
        for path in self.protected_paths or []:
            scope_path(path)
        # Exact argument arrays are approved, not interpolated shell snippets.
        if self.argv[0] not in {"python3", "python3.12", "node", "npm", "npx", "git", "cargo", "rustc"}:
            raise ValueError("Unsupported verification executable")
        return self


class WorkItem(StrictModel):
    id: str = Field(pattern=r"^[a-zA-Z0-9_-]{1,64}$")
    instruction: str = Field(min_length=1, max_length=8000)
    paths: list[str] = Field(default_factory=list, max_length=100)
    depends_on: list[str] = Field(default_factory=list, max_length=32)
    input_paths: list[str] = Field(default_factory=list, max_length=100)
    interfaces: list[str] = Field(default_factory=list, max_length=32)


class Limits(StrictModel):
    max_workers: int = Field(default=1, ge=1, le=2)
    repair_cycles: int = Field(default=2, ge=0, le=2)
    replans: int = Field(default=1, ge=0, le=1)
    wall_seconds: int = Field(default=900, ge=30, le=3600)
    model_calls: int = Field(default=60, ge=1, le=200)
    graph_steps: int = Field(default=30, ge=2, le=60)


class ExecutionSettings(StrictModel):
    checks: list[Check] = Field(min_length=1, max_length=20)
    work_items: list[WorkItem] = Field(min_length=1, max_length=32)
    limits: Limits = Field(default_factory=Limits)
    mode: Literal["implement", "diagnostic"] = "implement"
    task_type: Literal["investigation", "bug_fix", "feature", "refactor"] | None = None
    role_models: dict[str, str] = Field(default_factory=dict)
    guidance_ids: list[str] | None = None


class EnvironmentProfile(StrictModel):
    id: Literal["offline-linux-system-v2"] = "offline-linux-system-v2"
    fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    details: dict


class WorkflowBinding(StrictModel):
    task_type: Literal["investigation", "bug_fix", "feature", "refactor"]
    version: Literal[1] = 1
    fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    definition: dict
    models: dict[str, str]
    guidance: list[dict]


class TaskContract(ExecutionSettings):
    schema_version: Literal[2] = 2
    version: int = Field(ge=1)
    proposal_version: int = Field(ge=1)
    source_revision: str = Field(pattern=r"^[a-f0-9]{40,64}$")
    model: str
    policy_version: Literal["local-bwrap-v2"] = POLICY_VERSION
    proposal: Proposal
    environment: EnvironmentProfile
    workflow: WorkflowBinding
    protected_inputs: dict[str, tuple[str, bool]]

    @model_validator(mode="after")
    def validate_plan(self):
        if self.proposal.unresolved_questions:
            raise ValueError("Resolve proposal questions before drafting an executable contract")
        paths = self.proposal.affected_paths
        if not paths and self.mode == "implement":
            raise ValueError("Execution requires explicit affected paths")
        if self.mode == "diagnostic" and (paths or any(i.paths for i in self.work_items)):
            raise ValueError("Diagnostic contracts cannot grant source writes")
        if self.workflow.task_type == "investigation" and self.mode != "diagnostic":
            raise ValueError("Investigation execution requires a diagnostic contract")
        if self.workflow.task_type == "refactor" and not self.proposal.preserved_behavior:
            raise ValueError("A refactor must identify preserved behavior")
        if self.workflow.task_type in {"bug_fix", "feature"} and not self.proposal.changed_behavior:
            raise ValueError("A bug fix or feature must identify changed behavior; revise legacy proposals explicitly")
        if self.workflow.task_type == "refactor" and not any(check.baseline_requirement == "pass" for check in self.checks):
            raise ValueError("A refactor requires a passing characterization check")
        if self.mode == "implement" and any(check.expected_exit_code != 0 for check in self.checks):
            raise ValueError("Implementation checks must succeed; nonzero expectations are diagnostic only")
        if not all(value.strip() for value in self.proposal.acceptance_criteria):
            raise ValueError("Acceptance criteria cannot be blank")
        if self.task_type != self.workflow.task_type or self.role_models != self.workflow.models:
            raise ValueError("Workflow selection and role models disagree")
        if digest(self.environment.details) != self.environment.fingerprint:
            raise ValueError("Environment fingerprint is inconsistent")
        if digest({"definition": self.workflow.definition, "models": self.workflow.models,
                   "guidance": self.workflow.guidance}) != self.workflow.fingerprint:
            raise ValueError("Workflow fingerprint is inconsistent")
        for path in self.protected_inputs:
            scope_path(path)
        for path in paths:
            scope_path(path)
        ids = [item.id for item in self.work_items]
        if len(set(ids)) != len(ids) or len({c.id for c in self.checks}) != len(self.checks):
            raise ValueError("Work item and check IDs must be unique")
        if any(not set(check.affected_items) <= set(ids) for check in self.checks):
            raise ValueError("Verification references an unknown work item")
        visited = set()
        pending = {item.id: item for item in self.work_items}
        for item in self.work_items:
            if self.mode == "implement" and not item.paths:
                raise ValueError("Implementers require owned paths")
            for path in item.input_paths:
                scope_path(path)
            if any(not name.strip() or len(name) > 128 for name in item.interfaces):
                raise ValueError("Invalid shared interface identity")
            if len(set(item.depends_on)) != len(item.depends_on) or not set(item.depends_on) <= set(ids):
                raise ValueError("Unknown or duplicate work dependency")
            for path in item.paths:
                scope_path(path)
                if not any(contains(scope, path.rstrip("/")) and (not path.endswith("/") or scope.endswith("/")) for scope in paths):
                    raise ValueError("Worker ownership exceeds approved scope")
        while pending:
            ready = [key for key, item in pending.items() if set(item.depends_on) <= visited]
            if not ready:
                raise ValueError("Execution graph contains a cycle")
            for key in ready:
                visited.add(key)
                pending.pop(key)
        if not all(any(contains(scope, path.rstrip("/")) for item in self.work_items for scope in item.paths) for path in paths):
            raise ValueError("Every affected path needs a worker owner")
        by_id = {item.id: item for item in self.work_items}
        for item in self.work_items:
            ancestors = set(item.depends_on)
            while True:
                expanded = ancestors | {dep for key in ancestors for dep in by_id[key].depends_on}
                if expanded == ancestors:
                    break
                ancestors = expanded
            for producer in self.work_items:
                if producer.id != item.id and overlaps(producer.paths, item.input_paths) and producer.id not in ancestors:
                    raise ValueError("Declared producer/consumer inputs require an execution dependency")
        return self


class WorkerReport(StrictModel):
    summary: str = Field(min_length=1, max_length=8000)
    needs_amendment: bool = False
    reason: str = Field(default="", max_length=4000)
    observations: list[str] = Field(default_factory=list, max_length=20)
    limitations: list[str] = Field(default_factory=list, max_length=20)


class DiagnosticReport(WorkerReport):
    observations: list[str] = Field(min_length=1, max_length=20)
    limitations: list[str] = Field(min_length=1, max_length=20)


class Coverage(StrictModel):
    criterion: int = Field(ge=0)
    check_ids: list[str] = Field(min_length=1)
    explanation: str = Field(min_length=1, max_length=4000)


class Review(StrictModel):
    verdict: Literal["pass", "changes_required", "needs_amendment"]
    summary: str = Field(min_length=1, max_length=8000)
    findings: list[str]
    coverage: list[Coverage]
    affected_items: list[str] = Field(default_factory=list)
    already_satisfied: bool = False
