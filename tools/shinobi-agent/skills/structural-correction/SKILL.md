---
name: structural-correction
description: 'Prevent an evidenced recurring mechanical error with a narrowly scoped structural change and demonstrate that it catches the original failure.'
---

# Structural correction

Use a concrete repeated failure or explicit correction request. Read its evidence and relevant implementation before choosing a fix. Product ambiguity is not solved by a lint rule.

1. Identify the error's cause and where prevention belongs: type/interface design, validation, test fixture, automated check, safer helper or instruction discovery.
2. Prefer a structure that makes the invalid action impossible or detectably wrong over another generic reminder. Keep legitimate use cases possible.
3. Specify the allowed scope and the observable before/after behavior. Do not install unrelated tooling or refactor neighboring systems as a cleanup opportunity.
4. Implement the authorized correction and replay the original failure. Establish that the check rejects it for the intended reason, then verify a valid case still succeeds.
5. Assess false positives, bypass paths and maintenance burden. Retain the original evidence and explain what remains unprevented.

Output: a targeted correction with negative and positive evidence. Changes to Shinobi's governing skills or protected checks require their own approved maintenance task; a failing product run cannot alter its own rules. Use `failure-correction` for ordinary product repairs rather than invoking this broader maintenance workflow.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
