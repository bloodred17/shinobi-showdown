"""The small, versioned transport and proposal contract for Slice 1."""

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Request(StrictModel):
    version: Literal[1] = 1
    request_id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")
    operation: Literal["create", "resume", "list", "chat", "contract", "approve", "status", "pause", "cancel", "continue", "steer", "recover"]
    session_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")
    repository: str | None = None
    revision: str = Field(default="HEAD", min_length=1, max_length=256)
    query: str | None = Field(default=None, max_length=48000)
    contract_hash: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    run_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")
    execution: dict | None = None

    @model_validator(mode="after")
    def required_fields(self):
        if self.operation == "create" and not self.repository:
            raise ValueError("create requires an explicit repository path")
        if self.operation not in {"create", "list"} and not self.session_id:
            raise ValueError("operation requires a session_id")
        if self.operation == "chat" and not (self.query and self.query.strip()):
            raise ValueError("chat requires a non-empty query")
        if self.operation == "approve" and not self.contract_hash:
            raise ValueError("approval requires the displayed contract hash")
        if self.operation == "steer" and not (self.query and self.query.strip()):
            raise ValueError("steering requires an instruction")
        return self


class Citation(StrictModel):
    path: str = Field(min_length=1, max_length=1024)
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    claim: str = Field(min_length=1, max_length=4000)


class Proposal(StrictModel):
    objective: str = Field(min_length=1, max_length=4000)
    constraints: list[str]
    exclusions: list[str]
    approach: list[str] = Field(min_length=1)
    affected_paths: list[str]
    acceptance_criteria: list[str] = Field(min_length=1)
    unresolved_questions: list[str]
    checks: list[dict] = Field(default_factory=list)
    work_items: list[dict] = Field(default_factory=list)


class Outcome(StrictModel):
    kind: Literal["answer", "needs_input", "proposal"]
    message: str = Field(min_length=1, max_length=12000)
    questions: list[str]
    evidence: list[Citation]
    proposal: Proposal | None

    @model_validator(mode="after")
    def consistent_outcome(self):
        if self.kind == "needs_input" and not self.questions:
            raise ValueError("needs_input must include a question")
        if self.kind == "proposal":
            if self.proposal is None or not self.evidence:
                raise ValueError("a repository-grounded proposal needs a proposal and evidence")
        elif self.proposal is not None:
            raise ValueError("only proposal outcomes may contain a proposal")
        return self
