---
name: requirements-interview
description: 'Resolve material product choices in dependency order and distinguish user requirements from researched facts and assumptions.'
---

# Requirements interview

Input: original user turns, relevant source and existing accepted decisions. Build a decision graph: which answer would make later questions unnecessary or change their options? Ask the current independent questions together; defer questions whose premises are unresolved.

1. Inspect facts the repository can answer: existing behavior, consumers, constraints, tests and deployment assumptions. Ask the user about intent or unavailable facts, not information you can read.
2. For each material choice, explain the concrete consequence, offer a recommendation with its reason, and make the alternatives distinguishable. Do not overwhelm the user with every conceivable edge case.
3. Exercise answers using a normal example and a boundary or failure example. Probe contradictions: who may act, what state changes, how failure is visible, what compatibility must remain, and what is outside this request.
4. Update dependent choices when an answer changes. Keep rejected alternatives and the decisive reason when later workers could otherwise reopen them.
5. Summarize the resulting behavior and unresolved decisions. Do not use a self-assigned confidence percentage as a stopping rule. Stop when further questions would not materially change the agreed result.

Record explicit requirements with their original `source_turn` and verbatim `source_quote`; mark interpretations as inference. Preserve stable IDs when wording is clarified, advance the record revision for changed requirements and record supersession when direction changes. Already granted authorization is not another unanswered interview question. Material changes to an approved contract return for amendment.

Output: a grounded requirements record and the remaining decisions, if any. No repository write or authority is implied by an interview.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
