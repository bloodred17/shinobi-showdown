---
name: task-decomposition
description: 'Split an accepted specification into independently verifiable slices with ownership, acceptance and real dependency edges.'
---

# Task decomposition

Read the specification, glossary, relevant interfaces and verification constraints. Each task must fit a fresh worker context and deliver a complete observable slice, not just finish one technical layer while leaving behavior unusable.

1. Identify the smallest meaningful end-to-end result. Describe what it delivers, linked requirements and scenarios, owned paths, inputs, interfaces and exact verification. Include relevant original requirements in the brief rather than relying on a task title.
2. Add dependencies only where a producer's output or accepted interface is needed. A consumer reading another task's owned output must name that dependency. Check cycles, missing producers and overlapping ownership before proposing concurrency.
3. Size by reasoning and integration risk, not arbitrary line counts. Split a task whose context or verification cannot be handled coherently; combine tasks whose artificial separation creates constant coordination.
4. For wide mechanical migrations, use expand, migrate consumers in verifiable batches, then contract. Intermediate breakage requires an explicitly isolated integration boundary and a final verification task; do not promise independently green slices that cannot exist.
5. Review coverage: every task serves an accepted scenario; every required scenario has an owner and check; exclusions do not justify work. Include integration verification and affected documentation in scope when necessary.
6. Present the dependency-ready frontier and explain granularity. Incorporate user changes before the first exact contract is approved. Do not publish tickets to an external tracker or maintain a second task database.

Output: work items, assignments and dependency edges in Shinobi's existing plan, with selection rationale and unresolved feasibility gaps. New regression tests use separately owned test-only tasks and admission checks when required by the runtime.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
