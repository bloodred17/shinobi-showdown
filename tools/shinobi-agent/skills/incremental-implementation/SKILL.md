---
name: incremental-implementation
description: 'Implement one verifiable behavior slice at a time and re-ground the remaining plan when observed results contradict assumptions.'
---

# Incremental implementation

Begin with the approved assignment, linked requirements, current source and accepted dependencies. Identify the smallest working path that demonstrates progress toward its acceptance criteria.

1. Inspect the existing implementation and tests before editing. Reuse patterns whose behavior fits the requirement; do not add speculative infrastructure for imagined future needs.
2. State what the next slice changes and what stays invariant. For behavior work, use `behavior-tdd`; for a refactor, characterize preserved behavior before restructuring.
3. Make the slice within owned paths. Keep related public interfaces and consumers coherent; avoid leaving unrelated half-built branches of a feature.
4. Run the approved focused checks and inspect the actual diff. Compare the outcome with the original scenario, including errors and relevant side effects. Do not expand testing indefinitely after the relevant checks pass without a new concern.
5. At a meaningful boundary, record what is now true, evidence, remaining work and assumptions disproved. If a new requirement or architectural choice is needed, surface it instead of silently adjusting the goal.
6. On failure, use `failure-correction` to classify the problem. Repeated ineffective patches are a reason to diagnose, not to broaden the change.

Output: a coherent slice and truthful WorkerReport with observations and limitations. Local checks are advisory until integrated verification. Keep cleanup/refactoring separate from the active red-green cycle; only perform separately justified simplification within approved scope. Do not equate number of edited files with completion.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
