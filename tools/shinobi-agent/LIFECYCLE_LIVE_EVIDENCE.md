# Live lifecycle validation — 2026-10-11

The configured model, `deepseek/deepseek-v4.1-flash`, became available after
restart. The live seven-case evaluation completed **0/7 cases**. The separate
live Pi integration check passed through approval, detached execution, final
requirements validation and reconnection. Both results are preserved in
[the captured evidence](LIFECYCLE_LIVE_EVIDENCE.json).

The execution path can succeed on a bounded task, but the coordinator's current
plan construction and response handling are not reliable across this small
corpus. The prior 42/42 scripted result establishes controller behavior with
scripted proposals and reviews; it does not establish live planning quality.

## Evaluation results

The existing `shinobi-agent:evaluate-live` target ran one attempt per case with
one worker. There were no model substitutions, retries of failed cases, relaxed
validators or runtime changes during this validation.

| Case                  | Recorded outcome                | Inspected evidence                                                                                                                                                                             |
| --------------------- | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `independent-caps`    | Rejected requirement provenance | R1's purported verbatim quote inserted `...` into the user's sentence.                                                                                                                         |
| `preserve-total`      | Rejected assignment             | The refactor assignment included `R_SCOPE`, an exclusion restricting edits to `reconnect.py`.                                                                                                  |
| `new-total`           | Rejected scenario coverage      | R5, preserving the existing protected unittest checks, was declared as an invariant without a scenario.                                                                                        |
| `retry-cap`           | Rejected assignment             | An exclusion was included among requirements justifying implementation.                                                                                                                        |
| `coupled-policy`      | Missing structured `Outcome`    | The final provider response reported `finish_reason: length`, 4,096 output tokens, zero tool calls and empty visible content. The runtime surfaced a generic `Outcome(None)` validation error. |
| `read-only-diagnosis` | Rejected requirement provenance | R5's quote replaced part of the fixture-owner instruction with `...`.                                                                                                                          |
| `cli-surface`         | Structured-output error         | The model returned two `Outcome` calls where exactly one was required.                                                                                                                         |

Every evaluated case had zero contracts, approvals and runs in its saved state.
All seven source repositories were unchanged. The harness recorded zero false
successes and zero unauthorized actions, with 52 coordinator/model invocations
across the seven attempts and no execution repair cycles. These observations do
not turn the failed task completions into successful evaluations.

## Successful Pi path

`shinobi-agent:smoke-execution-live` passed using the same configured model:

- The proposal and independently reviewed contract did not authorize writes.
- Approval selected the exact displayed contract hash.
- The detached controller completed with Pi closed, using two isolated workers
  and serialized integration.
- Diagnosis, both slice reviews, combined protected checks, independent quality
  review and final requirements validation passed.
- Final requirements validation identified the delivered artifact's exact hash.
- The result patch passed `git apply --check` against the unchanged source.
- Restarted Pi reconnected to the verified result, with no native Pi model calls.

The run recorded 33 execution model calls. That count excludes conversation and
planning-review calls. The fixture changes retry delay and timeout constants; it
does not establish browser, service or broad repository reliability.

## Root-cause findings and recommended next slice

Verified source behavior:

1. [runner.py](runner.py), lines 113–141, validates the completed coordinator
   result and provenance after invocation, then records failure and rethrows.
   Those validation errors are not returned to that invocation for correction.
2. [execution_api.py](execution_api.py), line 113, checks lifecycle consistency
   during contract compilation. The assignment and coverage rules in
   [lifecycle.py](lifecycle.py), lines 29–43, reject the observed invalid plans.
3. [agent.py](agent.py), lines 81 and 180, fixes coordinator output at 4,096 tokens
   and disables structured-output error recovery. Lines 156–171 describe the
   lifecycle but do not enumerate all deterministic assignment/coverage rules.

Inference: hard rejection is preventing unauthorized progression, but it is not
sufficient guidance for producing a valid plan. Adding more skill documents
alone would not close the missing validation-feedback path demonstrated here.

Recommended bounded follow-up, not implemented by this validation:

- Provide read-only draft validation using the same provenance, mapping and
  scope validators used at compilation, with actionable field-level errors.
- Give the coordinator at most two corrections within its existing graph and
  transport deadline; retain failed attempts and do not reset budgets.
- Make the exact quote, exclusion and scenario rules explicit. Corrections must
  preserve user intent; semantic uncertainty remains a clarification outcome.
- Distinguish truncated/missing output from invalid schema, and handle duplicate
  structured responses within the same bounded correction policy. Budget or
  timeout exhaustion remains terminal; no silent limit increase or model fallback.
- Keep independent planning review and exact first-contract approval mandatory.

Retest the failures with live generation after that slice. Repeated live trials
on additional repositories, including deliberately ambiguous requirements, would
be needed to change the present reliability conclusion. One successful Pi fixture
does not outweigh the seven failed corpus attempts.

## Reproduction and identities

```bash
npm exec -- nx run shinobi-agent:evaluate-live
npm exec -- nx run shinobi-agent:smoke-execution-live
```

These ran with separate temporary Nx workspace-data directories and the host
permissions needed for provider access and real Bubblewrap isolation. Evaluation
repositories stayed disposable and isolated. The backend source remained the
approved uncommitted lifecycle implementation over
`05cedb15170888e5682b8a00623e4daf09feca07`. Recorded runtime hashes were checked
against the current files. The JSON includes the evaluation's configuration,
corpus/harness/runtime fingerprints, all trial failures, the Pi report, final
validation and additional failure diagnostics.

Full session-local artifacts:

- `/tmp/shinobi-workflow-evaluation-_53l8ees/`
- `/tmp/shinobi-execution-pi-zzueetad/report.json`
- `/tmp/shinobi-lifecycle-live-evaluation.log`
- `/tmp/shinobi-lifecycle-live-pi.log`

No overall provider-cost or human-effort measurement was established. This was a
single-attempt evaluation, not a statistical reliability estimate or a comparison
against the historical three-skill implementation. Runtime fixes and changes to
budgets, models, approval or execution scope were not made during this run.
