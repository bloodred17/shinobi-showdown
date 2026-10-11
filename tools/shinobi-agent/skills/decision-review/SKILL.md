---
name: decision-review
description: 'Challenge a consequential plan, interface or implementation decision with independent evidence before dependent work compounds a mistake.'
---

# Decision review

Use at a risky decision or when new evidence contradicts the current approach, not after every trivial edit. Define the artifact and precise requirements to assess.

1. Prepare an independent review brief with the original relevant requirements, constraints, source/candidate identity and artifact. Do not prime the reviewer with the author's preferred conclusion or persuasive defense.
2. Inspect assumptions, missing requirements, boundary conditions, simpler viable alternatives and evidence that could falsify the proposed design. Findings need a concrete consequence and supporting source or reproducible observation.
3. Reconcile each finding: accept and correct, reject with counter-evidence, or leave unresolved with the missing evidence identified. Agreement among reviewers does not outweigh one reproducible defect.
4. Correct only the affected decision or implementation. Rerun relevant verification and ensure dependent tasks receive the changed premise.
5. Bound the loop by the contract's remaining budgets and repair limits. If disagreement reflects an unresolved product choice or changed scope, return for clarification/amendment rather than repeating reviews until one approves.

The current runtime supplies independent planning, slice and final reviews. Use those mechanisms and configured models; this skill grants no ability to spawn agents or call external CLIs. If only a self-check is available, label it as such rather than claiming independent review.

Output: specific findings, their disposition, evidence and implications for the remaining plan. Preserve unresolved risks; a confident reviewer summary cannot replace a missing acceptance check.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
