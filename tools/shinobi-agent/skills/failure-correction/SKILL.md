---
name: failure-correction
description: 'Classify a failed check or review, investigate its cause and return to the responsible stage instead of blindly patching or weakening tests.'
---

# Failure correction

Capture the exact failure, command, input revision, environment and relevant logs before changing anything. Stop work that depends on the failed assumption.

1. Reproduce the observation with the same input and environment where possible. Distinguish a behavioral failure from harness, dependency, provider or environment failure.
2. Classify the issue: implementation, diagnosis, plan, test design, requirement or environment. A missing product decision is not an implementation bug, and an invalid test does not justify silently changing its expected result.
3. Form competing causal hypotheses and the smallest discriminating observation. Trace the affected path, reduce the example and change one relevant factor at a time. Use `bug-diagnosis` for stubborn or intermittent failures.
4. Apply a targeted fix only when it fits the approved implementation scope and remaining repair budget. Preserve failed observations and explain why the new action addresses the cause.
5. Repeat the original reproduction and relevant regression checks on the corrected artifact. A different check passing does not show that the original failure was fixed.
6. If a correction needs changed requirements, ownership, check oracle, permissions or unavailable infrastructure, return the specific amendment or capability gap. Do not hide a failure behind retries, lower thresholds or a substitute surface.

Output: classified findings, supported causal explanation, corrective action, re-verification and unresolved limits. Recurring process improvements belong to separately scoped maintenance, not self-modification of the governing skills during a run.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
