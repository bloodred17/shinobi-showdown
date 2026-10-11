"""Requirement lineage and stage outputs. These records never grant authority."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Requirement(Record):
    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
    statement: str = Field(min_length=1, max_length=2000)
    kind: Literal["behavior", "invariant", "exclusion"] = "behavior"
    origin: Literal["user", "inference"]
    source_turn: str = Field(min_length=1, max_length=128)
    source_quote: str = Field(min_length=1, max_length=4000)


class Decision(Record):
    id: str = Field(min_length=1, max_length=64)
    choice: str = Field(min_length=1, max_length=2000)
    rationale: str = Field(min_length=1, max_length=2000)
    requirement_ids: list[str] = Field(min_length=1, max_length=100)
    depends_on: list[str] = Field(default_factory=list, max_length=32)
    status: Literal["proposed", "unresolved"] = "proposed"


class RequirementRecord(Record):
    revision: int = Field(ge=1)
    requirements: list[Requirement] = Field(min_length=1, max_length=100)
    glossary: dict[str, str] = Field(default_factory=dict, max_length=50)
    decisions: list[Decision] = Field(default_factory=list, max_length=32)
    uncertainties: list[str] = Field(default_factory=list, max_length=32)
    supersedes: dict[str, str] = Field(default_factory=dict, max_length=100)

    @model_validator(mode="after")
    def identities(self):
        ids = [r.id for r in self.requirements]
        if len(ids) != len(set(ids)):
            raise ValueError("Requirement IDs must be unique")
        decisions = {d.id: d for d in self.decisions}
        if len(decisions) != len(self.decisions):
            raise ValueError("Decision IDs must be unique")
        done = set()
        for decision in self.decisions:
            if not set(decision.requirement_ids) <= set(ids) or not set(decision.depends_on) <= decisions.keys():
                raise ValueError("Unknown requirement or decision dependency")
        while len(done) < len(decisions):
            ready = {key for key, value in decisions.items() if set(value.depends_on) <= done} - done
            if not ready:
                raise ValueError("Decision dependencies contain a cycle")
            done |= ready
        return self


class Scenario(Record):
    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
    requirement_ids: list[str] = Field(min_length=1, max_length=100)
    criterion: int = Field(ge=0, strict=True)
    given: str = Field(min_length=1, max_length=2000)
    action: str = Field(min_length=1, max_length=2000)
    expected: str = Field(min_length=1, max_length=2000)
    side_effects: list[str] = Field(default_factory=list, max_length=20)
    surface: str = Field(min_length=1, max_length=256)
    check_ids: list[str] = Field(min_length=1, max_length=20)


class Assignment(Record):
    item_id: str
    requirement_ids: list[str] = Field(min_length=1, max_length=100)
    scenario_ids: list[str] = Field(min_length=1, max_length=100)


class TestAdmission(Record):
    """A test-only producer must finish before a dependent implementation starts."""
    item_id: str
    paths: list[str] = Field(min_length=1, max_length=32)
    scenario_ids: list[str] = Field(min_length=1, max_length=100)
    check_ids: list[str] = Field(min_length=1, max_length=20)


class LifecyclePlan(Record):
    requirements: RequirementRecord
    scenarios: list[Scenario] = Field(min_length=1, max_length=100)
    assignments: list[Assignment] = Field(min_length=1, max_length=32)
    test_admissions: list[TestAdmission] = Field(default_factory=list, max_length=16)
    selection_reason: str = Field(min_length=1, max_length=2000)


class Finding(Record):
    category: Literal["implementation", "diagnosis", "plan", "test_design", "environment", "requirements"]
    requirement_ids: list[str] = Field(min_length=1)
    explanation: str = Field(min_length=1, max_length=4000)


class RequirementAssessment(Record):
    requirement_id: str
    explanation: str = Field(min_length=1, max_length=4000)


class StageReview(Record):
    verdict: Literal["pass", "changes_required", "needs_amendment"]
    summary: str = Field(min_length=1, max_length=4000)
    coverage: list[RequirementAssessment] = Field(min_length=1, max_length=100)
    findings: list[Finding] = Field(default_factory=list, max_length=30)


class Diagnosis(Record):
    symptom: str = Field(min_length=1, max_length=2000)
    check_ids: list[str] = Field(min_length=1, max_length=20)
    hypotheses: list[str] = Field(min_length=1, max_length=5)
    observations: list[str] = Field(min_length=1, max_length=20)
    supported_cause: str = Field(min_length=1, max_length=2000)
    verdict: Literal["supported", "inconclusive", "already_satisfied"]
