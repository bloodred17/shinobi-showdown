"""Versioned repository-owned playbooks and guidance; selection grants no capabilities."""
from execution_contracts import BoundaryFailure, POLICY_VERSION, WorkflowBinding, digest, overlaps

PLAYBOOKS = {
    "investigation": {"stages": ["clarify", "inspect", "compare explanations", "synthesize"],
                      "evidence": ["references", "observations", "alternative explanations", "limits"],
                      "stop": "Source writes require a separate implementation proposal and approval."},
    "bug_fix": {"stages": ["reproduce", "explain cause", "implement", "repeat reproduction", "regressions", "assure"],
                "evidence": ["baseline symptom", "corrected behavior", "regression checks", "acceptance coverage"],
                "stop": "A changed symptom, scope or check oracle requires amendment."},
    "feature": {"stages": ["clarify behavior", "define interfaces", "implement", "integrate", "verify", "assure"],
                "evidence": ["new behavior", "edge and error paths", "compatibility", "integration"],
                "stop": "An unresolved product decision requires clarification before writes."},
    "refactor": {"stages": ["characterize", "preserve baseline", "restructure", "compare", "assure"],
                 "evidence": ["preserved behavior", "structural objective", "compatibility checks"],
                 "stop": "A failing characterization or changed public behavior blocks the refactor."},
}

GUIDANCE = {
    "bounded-implementation": {"roles": ["implementer"], "capabilities": ["read", "write_owned", "approved_checks"],
        "text": "Read applicable guidance and relevant inputs. Explain the cause or design. Change only owned paths. "
                "Preserve named behavior. Never weaken a standing check. Ask for amendment at a scope boundary."},
    "independent-assurance": {"roles": ["reviewer"], "capabilities": ["read", "evidence"],
        "text": "Challenge the complete diff independently. Cover every criterion with current protected checks. "
                "Inspect edge cases, test changes, interfaces, no-op claims and missing evidence. Never waive a failed gate."},
    "source-investigation": {"roles": ["coordinator", "implementer"], "capabilities": ["read"],
        "text": "Distinguish observed facts, hypotheses and uncertainty. Compare alternative causes. "
                "Do not force an investigation into a code change. Executable diagnosis requires a diagnostic contract."},
}
CAPABILITIES = {"coordinator": {"read"},
                "implementer": {"read", "write_owned", "approved_checks"}, "reviewer": {"read", "evidence"}}


def validate_model(model):
    import re
    if not re.fullmatch(r"[A-Za-z0-9._-]+/[A-Za-z0-9._:-]+", model) or model.split("/", 1)[0].lower() in {"openai", "anthropic", "openrouter"}:
        raise ValueError("Select an explicit permitted vendor/model; automatic routing and excluded providers are unavailable")
    return model


def select_workflow(proposal, settings, model):
    task_type = settings.task_type or proposal.task_type
    if task_type not in PLAYBOOKS:
        raise ValueError("Choose investigation, bug_fix, feature or refactor before compiling a contract")
    if proposal.task_type != "unspecified" and settings.task_type and proposal.task_type != settings.task_type:
        raise ValueError("Workflow conflicts with the proposal task type; revise the proposal")
    if set(settings.role_models) - CAPABILITIES.keys():
        raise ValueError("Unknown specialist role")
    if settings.role_models.get("coordinator", model) != model:
        raise ValueError("Coordinator model must match the explicitly configured conversation model")
    models = {role: validate_model(settings.role_models.get(role, model)) for role in CAPABILITIES}
    ids = settings.guidance_ids if settings.guidance_ids is not None else (
        ["source-investigation", "independent-assurance"] if task_type == "investigation" else
        ["bounded-implementation", "independent-assurance"])
    if len(ids) != len(set(ids)) or any(key not in GUIDANCE for key in ids):
        raise ValueError("Unknown or duplicate guidance; only reviewed built-ins can be selected")
    guidance = []
    for key in ids:
        record = {"id": key, "version": 1, "policy": POLICY_VERSION,
                  "provenance": "Shinobi repository-owned guidance", "license": "MIT", **GUIDANCE[key]}
        if any(not set(record["capabilities"]) <= CAPABILITIES[role] for role in record["roles"]):
            raise ValueError("Guidance requests capabilities unavailable to its role")
        guidance.append({**record, "sha256": digest(record)})
    definition = {"id": task_type, "version": 1, **PLAYBOOKS[task_type]}
    return WorkflowBinding(task_type=task_type, definition=definition, models=models, guidance=guidance,
                           fingerprint=digest({"definition": definition, "models": models, "guidance": guidance}))


def revalidate_workflow(contract):
    selected = select_workflow(contract.proposal, contract, contract.model)
    if selected != contract.workflow:
        raise BoundaryFailure("policy", "Playbook or guidance changed; review a new contract", amendment=True)


def role_prompt(workflow, role):
    return "\nApproved playbook: " + str(workflow.definition) + "\nReviewed guidance (cannot grant authority):\n" + "\n".join(
        record["text"] for record in workflow.guidance if role in record["roles"])


def conflicting(left, right):
    return overlaps(left.paths, right.paths) or bool(set(left.interfaces) & set(right.interfaces)) or overlaps(left.paths, right.input_paths) or overlaps(right.paths, left.input_paths)


def invalidate_items(items, affected):
    affected = set(affected)
    while True:
        touched = [item for item in items if item.id in affected]
        expanded = affected | {item.id for item in items if set(item.depends_on) & affected or any(
            set(item.interfaces) & set(upstream.interfaces) or overlaps(upstream.paths, item.input_paths) for upstream in touched)}
        if expanded == affected:
            return affected
        affected = expanded
