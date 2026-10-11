---
name: decision-documentation
description: 'Update affected documentation and preserve consequential design decisions when a change alters supported behavior or future engineering choices.'
---

# Decision documentation

Identify the actual audience and existing documentation conventions. Read the relevant docs and source before deciding what needs updating; a small internal edit need not create an ADR.

1. Update user-facing behavior, setup, API examples or operational instructions affected by the change. Verify command names, paths and examples against the current implementation.
2. For a consequential decision, record context, alternatives, chosen approach, decisive constraints, consequences and known limits. Preserve why a plausible alternative was rejected so future agents do not reopen it without new evidence.
3. Link the decision to the accepted requirement and relevant implementation. Keep one authoritative location rather than copying the same specification into several files.
4. Distinguish implemented, experimentally verified, proposed and unsupported behavior. Dated evidence retains the revision it tested; do not rewrite it as proof of a later implementation.
5. Review docs alongside the code for stale examples and accidental promises. If a required documentation path is outside the approved assignment, surface the needed scope change.

Output: focused documentation changes and, when warranted, a decision record in the project's existing format. Documentation cannot silently authorize a new capability or turn a roadmap item into implemented behavior. Preserve historical decisions with explicit supersession rather than erasing the reasons they were made.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
