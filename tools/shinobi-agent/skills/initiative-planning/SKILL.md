---
name: initiative-planning
description: 'Structure a large unclear initiative around dependent decisions before committing to implementation tickets.'
---

# Initiative planning

Inventory the intended outcomes, known constraints and unresolved decisions. Distinguish strategic questions from facts the repository can answer.

1. Map which decisions unlock or invalidate others. Investigate factual prerequisites first, then bring the user the current decision frontier with concrete tradeoffs.
2. Separate independently valuable capabilities, shared interfaces and uncertain experiments. Do not turn every possibility into an approved feature.
3. Keep a decision record with accepted choices, rejected alternatives, assumptions and evidence that would reopen them.
4. Once a capability is sufficiently understood, use `specification` and `task-decomposition` for that bounded slice. Keep unresolved later capabilities out of its execution contract.
5. Revisit the map when new evidence changes dependencies, preserving the original outcome and visible scope decisions.

Output: a capability/decision map, next decisions and a bounded next slice. This is for large ambiguous initiatives; a straightforward bug does not need this process. No extra task tracker or external publication is required.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
