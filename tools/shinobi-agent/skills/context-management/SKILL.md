---
name: context-management
description: 'Preserve original requirements, decisions and reliable evidence across task boundaries while keeping each worker context focused.'
---

# Context management

Build context around the worker's decision, not the entire conversation. Preserve the source of authority and meaning before compressing historical discussion.

1. Start with the current objective, relevant original user text, accepted requirement/scenario IDs, constraints, exclusions and current approval boundary. Include the accepted decision and why when reversal would cause drift.
2. Add the actual source revision, relevant files, interfaces, producer outputs, commands and observed failures. Separate facts, hypotheses, proposed actions and unrun checks explicitly.
3. Link larger artifacts only when the recipient has a readable local path or exposed resource. Keep the original requirement available; a sequence of summaries must not become the only source of intent.
4. Refresh context at natural boundaries: a completed slice, changed dependency, failed hypothesis, interruption or handoff. Retain unresolved questions, rejected explanations and the evidence that rejected them.
5. Remove stale duplicate narration, not still-applicable constraints. If a fact conflicts with the current repository or user correction, record the discrepancy and update the working interpretation visibly.
6. For a restart, verify state before continuing. A prior assistant's claim that tests passed is not current evidence; match revision, command, environment and result.

Output: a restartable task brief sufficient for an independent worker. Use `context-handoff` for an explicit handover. Context organization does not authorize new work, erase failed attempts or rewrite an accepted requirement to fit implementation.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
