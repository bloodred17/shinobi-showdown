---
name: context-handoff
description: 'Prepare a restartable handoff at interruption or ownership transfer, including actual state, unresolved decisions and next verification.'
---

# Context handoff

Read the original request, current accepted plan and actual repository state before summarizing. The recipient must be able to continue without guessing what the user approved.

Include:

- Goal and relevant original requirements; explicit constraints and non-goals.
- Accepted decisions and their reasons; unresolved choices and who can answer them.
- Source and candidate revisions, owned paths, dependencies and available artifact locations.
- Completed work with observable evidence; remaining work and the next concrete action.
- Exact checks run, their results and limitations. Distinguish baseline, worker-local and integrated evidence.
- Failed hypotheses and attempts that affect the next action, including environment failures.
- Approval status, remaining execution limits and conditions requiring amendment.

Keep it concise enough to use but do not replace important requirement text with an interpretation. Link large logs and diffs only at locations the recipient can access. Do not copy credentials into the handoff.

At resumption, inspect the current diff, input identities and pending control state; validate the handoff's claims against saved evidence. If source or authority changed, reconcile or request amendment before continuing. A handoff is neither a fresh grant of permission nor proof that a previous attempt succeeded.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
