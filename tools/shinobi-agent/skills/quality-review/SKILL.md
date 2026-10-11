---
name: quality-review
description: 'Review the actual candidate for correctness, security, maintainability, performance and testing without substituting quality for requirements validation.'
---

# Quality review

Fix the source baseline and candidate identity, read the diff and relevant surrounding code, and understand the accepted behavior. Scale review to the change's consequences.

Inspect five dimensions:

1. Correctness: invariants, errors, boundary values, resource lifetime, concurrency and compatibility.
2. Security: trust boundaries, authorization, input/output handling, secret exposure and abuse paths implicated by the change.
3. Maintainability: ownership, interface clarity, unnecessary coupling, duplicated logic and whether abstractions earn their complexity.
4. Performance: changed hot paths, resource growth and blocking work; request measurement rather than speculate about speed.
5. Testing: scenario coverage, independent expectations, realistic boundaries and checks weakened in the diff.

For each finding, cite the location, triggering condition, consequence and proposed correction. Separate blockers from preferences; do not demand unrelated cleanup. Existing conventions or measured requirements outweigh generic stylistic tastes.

Output: actionable findings and limitations. Verify fixes against current evidence. The separate `specification-review` establishes that the requested outcome was built; a quality pass cannot replace it.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
