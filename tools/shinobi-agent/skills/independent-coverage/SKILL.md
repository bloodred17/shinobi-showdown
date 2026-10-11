---
name: independent-coverage
description: 'Partition a broad review or verification task into independent coverage responsibilities with explicit methods and evidence.'
---

# Independent coverage

Define the common target revision, requirements and coverage question. Partition by meaningful risk or boundary, not by an arbitrary worker count.

1. Give each lane a unique responsibility, target identity, method, available inputs and expected evidence. Include relevant original requirements and a way to report missing capability.
2. Check for gaps and overlaps before dispatch. Shared state and non-isolated runtime instances may require sequential work.
3. Use only available configured workers within the contract limit. If parallel delegation is unavailable, execute the lanes sequentially and report that accurately.
4. Collect findings with source/command evidence and explicit unexamined areas. Do not treat an absent or failed lane as a pass.
5. Reconcile contradictory findings by reproducing decisive observations. Deduplicate reports without counting repeated claims as independent proof.

Output: coverage map, findings, evidence and gaps tied to the actual revision. Do not create ten lanes by default or infer completion from worker summaries alone. Code writes, external messages and model calls remain subject to their existing authority.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
