---
name: requirements-discovery
description: 'Coordinate requirements discovery when intent or terminology is unresolved; reuse established answers for a clear task.'
---

# Requirements discovery

Use the original request, follow-up corrections and relevant repository evidence. First decide what is missing: facts to inspect, choices only the user can make, or vocabulary whose ambiguity could change the design. A clear bounded request can go directly to specification; do not restart an interview already completed.

1. Read `requirements-interview` through `read_engineering_skill` when product choices remain. Maintain the dependency order of decisions rather than asking disconnected questions.
2. Read `domain-modeling` when competing meanings affect behavior, ownership or interfaces. Resolve these while questioning, so the specification uses agreed terms.
3. Keep a compact brief: intended outcome, users, explicit constraints, non-goals, resolved decisions, material assumptions and remaining questions. Preserve links to the original instruction turns; do not turn your interpretation into a quotation from the user.
4. Check a concrete normal scenario and the consequential failure or boundary scenario with the agreed terminology. If they contradict a decision, reopen that decision visibly.
5. Hand the brief to `specification`. A newly discovered ambiguity goes back to the responsible question, not to an invented implementation.

Completion means the material questions are answered or explicitly left blocking, the vocabulary is consistent, and the next stage can use the original requirements. This skill composes two local procedures; it is not a second requirements database or another approval ritual.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
