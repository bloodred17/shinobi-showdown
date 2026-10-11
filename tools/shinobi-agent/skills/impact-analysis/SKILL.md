---
name: impact-analysis
description: 'Trace the behavioral impact of a shared interface or state change beyond direct textual callers.'
---

# Impact analysis

Name the proposed change and the contract it could alter. Fix the repository revision and distinguish source callers from runtime consumers.

1. Inspect definitions, call sites, serialized formats, configuration, generated bindings, tests, background jobs and external-consumer assumptions where relevant.
2. Trace effects through state transitions, authorization, error handling and operational ownership. Text search alone misses dynamic dispatch and data compatibility.
3. Classify consumers: must change together, can coexist during migration, unaffected with evidence, or unknown. Identify shared paths and interfaces that constrain task ownership.
4. Propose verification at affected boundaries and a compatibility sequence. New out-of-scope consumers require a visible plan amendment rather than silent edits.
5. Record search coverage and unresolved paths so absence of a hit is not presented as proof that no consumer exists.

Output: affected contracts, consumers, dependency implications, tests and uncertainty. Feed the result into the task graph and review; do not automatically perform the refactor being assessed.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
