---
name: migration-planning
description: 'Plan compatibility-preserving changes to shared APIs or persisted data using consumer inventory, staged cutover and recovery.'
---

# Migration planning

Inventory producers, consumers, persisted representations and deployment order. Establish whether all consumers are controlled together or external/rolling compatibility is required.

1. Define old and new semantics, mapping rules and invariants. Identify irreversible transformations and evidence needed before cutover.
2. Expand with compatible new forms; migrate consumers or data in observable batches; contract only after evidence shows the old form is no longer required.
3. Specify ownership, idempotency, partial-failure behavior, reconciliation and recovery. Do not assume reverting code restores transformed data.
4. Keep each batch verifiable. If intermediate breakage is unavoidable, confine it to an explicitly approved isolated integration boundary and name where green is required.
5. Test representative old/new states, mixed-version behavior and failure recovery using authorized fixtures. Retain progress and validation evidence before deleting compatibility paths.

Output: dependency-aware migration tasks, acceptance checks, cutover criteria and recovery limits. A source search with no callers is insufficient evidence for deleting public APIs or production data. Execution and destructive cutover need their explicit approved scope.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
