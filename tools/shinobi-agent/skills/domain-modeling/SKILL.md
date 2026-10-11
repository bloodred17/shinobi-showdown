---
name: domain-modeling
description: 'Resolve ambiguous domain terms, identities, relationships and invariants when those distinctions affect the requested behavior.'
---

# Domain modeling

Use this when words such as account, user, session or approval refer to different concepts across the request and code. Reuse the project's vocabulary; do not rename a coherent model merely to match this skill.

1. Inventory the terms in the requirement, public interfaces, data structures and existing docs. Record each term's meaning, identity and lifecycle, with source examples. Identify synonyms and words with several meanings.
2. Describe relationships, cardinality, ownership and state transitions. Distinguish a durable entity from a value, event or temporary view only where that distinction affects the work.
3. Test the proposed meanings against concrete scenarios: creation, duplicate identity, transfer, expiry, deletion and failure as applicable. Ask about genuine product ambiguities; inspect implementation facts.
4. State the invariants the implementation must preserve. A relationship inferred from current code is evidence about today, not automatically the user's desired rule.
5. Propagate accepted terms into the requirements, scenarios and task instructions. If the model exposes a product choice, return it to the interview rather than burying it in naming.

Output: concise glossary entries, relationships, relevant invariants and unresolved conflicts. For persistent documentation, use existing conventions and approved paths; a glossary or ADR is warranted only when it prevents recurring ambiguity. Do not create a domain framework or refactor the code as a side effect of modeling.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
