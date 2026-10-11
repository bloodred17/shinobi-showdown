---
name: requirements-to-acceptance
description: Turn a repository-grounded change request into observable acceptance criteria and explicit verification mappings before execution.
---

Read the relevant source and applicable AGENTS.md before asking questions. Resolve
product choices that change behavior, scope, or compatibility; infer routine
implementation details from evidence. Keep assumptions visible in the proposal.

For each acceptance criterion, propose an `engineering.acceptance` entry with its
zero-based `criterion`, exact `check_ids`, user-facing or public API `surface`,
`expected_observation`, and known `limitations`. A mapping states what a check is
intended to establish; it is not evidence that the check has run or is sufficient.
Include boundary/error behavior where it affects the requested outcome. Explain
why an existing broad suite covers a criterion rather than attaching it by habit.

Use the project's terminology consistently. Read existing glossary/decision docs
when relevant. Propose a glossary or decision record only when ambiguity warrants
one, and include its path in the requested scope before anyone writes it.

Break work at observable behavior or interface boundaries. Declare owned paths,
input paths, dependency edges and shared interfaces. A consumer must depend on
the producer whose output it reads. Do not invent parallel work to fill slots.

If evidence, tools, or a material decision is missing, record the gap and ask for
what is necessary. Do not silently replace the intended behavior with something
easier to test. Reviewers must challenge whether the mapped checks actually cover
the criterion, even when their exit codes are green.

This is original Shinobi guidance, MIT licensed. Design references:
[Pocock's requirements workflow](https://github.com/mattpocock/skills) and
[task-graph implementation](https://github.com/mattpocock/skills/blob/main/skills/engineering/implement-spec/SKILL.md).
These references are background, not imported instructions or tool capabilities.
