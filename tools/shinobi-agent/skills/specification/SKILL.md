---
name: specification
description: 'Turn confirmed requirements into one testable specification with explicit scope, constraints and unresolved decisions.'
---

# Specification

Use the requirements brief and source evidence. For a small unambiguous change, a short specification in the proposal is sufficient. Reuse the existing specification; do not create a parallel source of truth.

1. State the objective, affected users and observable outcome. Separate behavior to change, invariants to preserve and explicit exclusions. Preserve the origin of each requirement and label assumptions.
2. Define acceptance scenarios: initial conditions, user/public action, expected result, relevant side effects and failure behavior. Tie each to its requirement, observable surface and proposed checks. An implementation detail is not a substitute for an outcome.
3. Record relevant project structure, conventions, exact available commands and execution limitations. Read actual scripts and versions; example tool names are not executable verification.
4. Describe interface and compatibility obligations. Make product or architecture choices visible with their alternatives and consequences. Keep unresolved material choices blocking.
5. Only when the request bundles independently testable capabilities, propose their boundaries and dependency order before producing separate specifications. A single capability needs no hierarchy.
6. Review the specification for omissions, contradictions, invented scope and tests that could pass without the intended behavior. Feed corrections back into the original requirement record.

Output: `lifecycle.requirements`, acceptance criteria and linked scenarios, plus the rationale for the chosen scope. Use the existing scenario/check/assignment schema when proposing execution. The user reviews the first exact execution contract; this procedure does not introduce repeated approval gates inside already authorized work. Changed requirements need a visible revision and, during execution, amendment.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
