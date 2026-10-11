---
name: workflow-retrospective
description: 'Diagnose recurring workflow friction from actual run evidence and propose targeted environment or procedure improvements.'
---

# Workflow retrospective

Begin with a completed or interrupted task's original requirement, run events, tool errors, decisions, diff and verification outcomes. Separate an agent mistake from an environment or instruction defect.

1. Identify concrete friction: repeated failed commands, missing information, ambiguous ownership, unnecessary questions, lost context or unverifiable completion claims. Cite the observed sequence and its consequence.
2. Trace the cause rather than merely restating the symptom. Check whether correct instructions existed, were discoverable, were contradictory or depended on unavailable tools.
3. Propose the smallest change that would prevent recurrence: a clearer trigger, focused reference, deterministic check, fixture or environment correction. Include the cost and the behavior that might be overconstrained.
4. Rank recommendations by demonstrated frequency and impact. Do not generalize one incidental case into a universal rule.
5. Separate accepted changes from suggestions and unresolved causes. Route procedural updates to `skill-improvement` and structural fixes to `structural-correction` only when authorized.

Output: evidenced causes and bounded recommendations with a validation scenario. This skill diagnoses the workflow; it does not automatically change project configuration, install tooling or rewrite skills during an unrelated task.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
