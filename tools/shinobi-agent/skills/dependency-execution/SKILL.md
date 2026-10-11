---
name: dependency-execution
description: 'Coordinate multiple approved dependent tasks using a ready frontier, isolated workers and verification of the integrated specification.'
---

# Dependency execution

Use for a multi-task plan. Read the accepted specification and task graph; let the existing controller own dispatch, isolated repositories, integration and budgets. This procedure does not create an independent swarm, reset user branches or open a PR.

1. Determine the ready frontier from completed dependencies. Confirm each worker's input revision and producer outputs match the current accepted integration state.
2. Give a worker its owned scope, original relevant requirements, scenarios, verification recipe and source pointers. Include global invariants and exclusions. A pointer is useful only if the worker can actually read its target.
3. Parallelize only independent work within the configured worker limit. Shared interfaces or overlapping ownership require sequencing even if textual dependency declarations omit them.
4. On completion, examine the diff and evidence against the task. Integrate through the controller, then unblock consumers. Do not equate the worker's completion statement with accepted integration.
5. If a producer changes during repair, invalidate affected consumers and recheck their assumptions. Preserve unrelated valid work where the controller supports it; do not claim selective recovery that is unavailable.
6. After all tasks, run combined checks and review the full specification. Locally successful tasks can still fail together or leave requirements uncovered.

Output: current task status, accepted integration state, evidence and remaining blockers. Resource cleanup applies only to controller-owned disposable state. Completion is the verified local result; applying it to the user's checkout, publication and deployment are separate actions.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
