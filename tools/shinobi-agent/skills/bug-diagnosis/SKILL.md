---
name: bug-diagnosis
description: 'Diagnose stubborn or intermittent failures with a sensitive reproducer, competing hypotheses and discriminating observations.'
---

# Bug diagnosis

Capture expected behavior from the requirement and actual behavior from evidence. Record the failing revision, input, environment and timing conditions; preserve the original failure before editing.

1. Reproduce the failure and reduce irrelevant factors without removing the symptom. For intermittent behavior, record attempts and conditions; one passing retry does not disprove the bug.
2. Trace the relevant path and propose competing causes. Each hypothesis must predict an observation that distinguishes it from alternatives.
3. Run the smallest approved discriminating check or inspect decisive source. Instrumentation requires owned paths and permitted execution; do not hotfix a live process under a read-only task.
4. Reject hypotheses contradicted by evidence and retain why. If observations are insufficient, identify the exact missing capability rather than assert a root cause.
5. When supported, describe the causal chain and minimal correction. Repeat the original reproduction and relevant regressions after a separately authorized fix.

Output: observations, hypotheses, predictions, causal conclusion and limits in the diagnosis schema. An inconclusive diagnostic remains inconclusive. A passing unrelated suite cannot establish that an intermittent symptom is resolved.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
