---
name: code-simplification
description: 'Simplify a verified implementation while preserving behavior, public contracts and independently established checks.'
---

# Code simplification

Use after behavior is green or for an explicitly approved refactor. Identify a concrete readability, duplication or coupling problem; smaller text alone is not the objective.

1. Establish passing characterization at the public boundary and identify behavior that must remain unchanged, including errors and side effects.
2. Remove unnecessary indirection, duplicated logic or dead branches when source and consumer evidence justify it. Prefer explicit cohesive code over clever compression.
3. Make a coherent scoped change, then rerun the same characterization and inspect the diff. Keep interface and data compatibility intact.
4. Stop when the identified problem is resolved. Do not broaden into stylistic cleanup, delete explanatory comments indiscriminately or lower checks to accommodate the refactor.
5. If behavior must change, return to requirements and authorization rather than classify the change as simplification.

Output: the structural improvement, unchanged behavior evidence and remaining limits. Keep this outside the active behavior-TDD red-green cycle and within owned paths.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
