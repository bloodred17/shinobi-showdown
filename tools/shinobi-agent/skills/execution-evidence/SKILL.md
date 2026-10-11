---
name: execution-evidence
description: 'Keep autonomous work reviewable by recording consequential decisions, evidence and unresolved outcomes as they occur.'
---

# Execution evidence

Use during unattended or extended work and when presenting the result. Keep a decision trail, not a transcript of every command and not reconstructed private reasoning.

1. At a meaningful choice, record the relevant requirement, options considered, chosen action and concise evidence-based reason. Include changes of direction and why the old premise no longer held.
2. Preserve command results and artifact references with the revision, environment and scenario they concern. Distinguish observed behavior, scripted model output, mocks, source inference and planned but unrun verification.
3. Record failed attempts, interruptions and unresolved questions when they affect confidence or the next action. Do not replace a failure with a later success on a different path.
4. For each completion claim, point to the actual current result. Report scope changes requiring amendment rather than presenting them as routine execution.
5. At handoff or delivery, reconcile the narrative with run state, diff and captured evidence. Remove unsupported claims, expose remaining gaps and summarize what the user can inspect.

Output: concise progress decisions and a final account of what changed, why, how it was verified and what remains uncertain. Use the controller's existing reports and artifacts; do not create duplicate event storage or send external updates. Credentials and unrelated personal data do not belong in evidence. Within approved autonomy, routine decisions continue without repeated permission prompts, while the record makes those decisions reviewable.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
