---
name: specification-review
description: 'Independently compare a plan or completed artifact with original requirements, keeping specification compliance separate from engineering quality.'
---

# Specification review

Fix the comparison baseline and candidate identity. Read original user instructions, accepted requirements, scenarios, exclusions and the actual relevant source/diff. Do not rely on the implementer's summary of what was requested.

1. For planning review, check omitted requirements, contradictions, invented work, feasible ownership/dependencies and whether proposed checks could distinguish correct from incorrect behavior.
2. For outcome review, walk each behavior and invariant to its implementation and current evidence. Check normal paths, consequential boundary/error paths and side effects. Identify acceptance claims supported only by source reasoning or an unrelated green suite.
3. Look for scope creep: extra features, changed defaults, compatibility breaks and architectural expansion not justified by the accepted request. Exclusions are constraints, not implementation tasks.
4. Keep Spec findings distinct from Standards findings. Use `quality-review` for engineering quality; passing it cannot excuse building the wrong thing. At final validation, compare the integrated result with the whole specification, not just individual worker slices.
5. Cite the exact requirement, source location and observation for each blocking issue. Explain the smallest correction or missing evidence; distinguish a defect from a preference.
6. Reassess corrected artifacts with current evidence. Do not reuse a pass tied to an older candidate or treat reviewer consensus as proof.

Output: requirement coverage, specific findings, verdict and limitations in the runtime's review schema. A no-op result needs explicit evidence that the requested behavior already holds. User acceptance, publication and applying the patch remain separate from this review.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
