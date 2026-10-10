# Approved local S1–S5 increment — 2026-10-10

The approved local implementation is complete for the documented offline Linux
system-tools profile. S6 remains planned pending cloud/VPC, GitHub identity and
permissions, shared storage, staging, retention and spending decisions. Nothing
was published, deployed, merged or applied to a user's source repository.

The inspected Git baseline was `5486550c029c84d8264718abc21ef7d0f1833fc7`.
This increment is uncommitted. The [captured JSON evidence](LOCAL_S5_EVIDENCE.json)
records tested controller/configuration hashes, fixture outcomes, check output,
patches and independent judgments. Historical evidence remains in
[EVIDENCE.md](EVIDENCE.md). Raw databases, checkpoints and terminal captures remain
in the referenced `/tmp` directories; the JSON snapshot preserves the selected
validation evidence independently of those directories.

## Implemented behavior

- S1 proposals explicitly classify investigation, bug fix, feature or refactor
  and name changed/preserved behavior.
- S2 schema-2 contracts bind the full effective authority to source, role models,
  reviewed workflow/guidance, measured environment and protected check inputs.
  Pi displays the complete contract. Draft check/assignment IDs are reconciled
  with the reviewed execution settings without changing proposal history.
  Old raw records remain inspectable; old approvals cannot acquire new authority.
- S3 measures system tool/controller identity and dependency metadata, rechecks
  drift, preserves committed-source isolation and supports approved read-only
  diagnostics. Recoverable source-read errors remain contained in the sandbox
  and consume the same bounded graph/model allowance.
- S4 captures baseline and combined evidence, freezes selected oracle files and
  modes, rejects empty/skipped/reduced unittest suites, distinguishes failure
  categories, and requires explicit independent evidence for a no-op. Recovery
  checks persisted baseline gates and identity, including interruption between
  saving results and enforcing their gate.
- S5 provides four playbooks, three original MIT guidance entries, explicit
  compatible role models, declared shared interfaces/input dependencies,
  input-manifest reconciliation and dependent repair invalidation. One worker
  remains the default. Worker context includes baseline results; assurance sees
  current integrated reports and retains parsed recommendations before gating.
  Diagnostics require nonempty observations/limitations, which Pi can display.
  The versioned corpus and comparison harness never adopt a policy automatically.

## Offline and scripted validation

The final runtime regression passed **60 Python tests, eight bridge tests,
typecheck, scoped lint, formatting and both actual scripted Pi flows**. The
unchanged POC also passed its eight bridge/five Python tests, Pi bridge smoke,
typecheck, lint and formatting in the combined baseline regression.

```bash
NX_DAEMON=false NX_ISOLATE_PLUGINS=false NX_NATIVE_COMMAND_RUNNER=false \
NX_WORKSPACE_DATA_DIRECTORY=/tmp/shinobi-s5-delivery-final-checks \
npm exec -- nx run-many -t test typecheck lint format-check \
  -p shinobi-agent --output-style=static

npm exec -- nx run shinobi-agent:evaluate --output-style=static
```

The final repeated evaluation passed **36/36 independently checked fixture
trials**: six cases, three repetitions each, one and two workers. It observed no
false successes or unauthorized source/scope changes. Only generation was
scripted; actual graphs, contracts, approvals, sandboxes, integration, combined
checks, assurance and fixture judges ran. Report:
`/tmp/shinobi-workflow-evaluation-k2cfd09p/evaluation.json`.

Negative cases cover protected-test weakening despite ownership, environment and
guidance drift, incompatible guidance/model choices, legacy authority, missing
dependencies, failed refactor characterization, empty/skipped suites, unsupported
no-ops, dependency/input/interface conflicts, missing assurance coverage, invalid
structured output, graph exhaustion, changed recovery baselines, and diagnostic
disclaimers without findings. Read-error recovery cannot escape source scope.

Scripted evidence does **not** establish model quality or parallel efficiency.
Comparison thresholds require at least three live repetitions per case/config,
held-out coverage, no false/unauthorized success, quality at least the sequential
baseline and 10% latency or known-cost improvement. No configuration was adopted.

## Live validation and retained failures

All live generation explicitly used `deepseek/deepseek-v4.1-flash` through
OpenRouter. The harnesses created nonsensitive synthetic repositories under
`/tmp`; they did not export the user's application source. Automatic approval
review initially rejected the command for possible sensitive-source export.
Read-only inspection established the fixture boundary, and the same bounded
targets were then allowed.

Live Pi conversation passed, including proposal revision, restart/resume,
read-only enforcement and zero Pi-native inference. The actual detached Pi
execution path also passed with two isolated workers, combined verification,
read-only assurance, a patch that applied cleanly, completion with Pi closed and
reconnect to the result. Multiple live attempts are retained in the JSON snapshot.

The first six-case live workflow run completed 2/6. It exposed conflicting draft
versus effective assignment IDs, unresolved fixture-oracle questions and invalid
structured/coverage responses. After reconciling IDs and supplying the selected
settings explicitly, the full run completed **5/6**: bug fix, feature, refactor,
independent work and coupled work all passed their independent fixture judges.
The diagnostic did not pass; it remained an evidence failure.

Subsequent diagnostic rejection exposed missing reviewer context, then a worker
report containing a no-edit disclaimer without substantive findings. Parsed
rejected reviews are now retained; diagnostics require explicit observations and
limits. An ordinary missing-file read previously stopped the graph and now
returns a visible, bounded tool error. A parallel worker also incorrectly treated
an advisory combined check awaiting its sibling as an amendment requirement;
the assignment boundary is now explicit. These were corrected within the approved
scope, without weakening verification or adding provider retries/fallbacks.

The final targeted diagnostic passed with required observations/limitations,
unchanged source and `diagnostic` disposition (16 coordinator/controller model
calls). The final actual Pi detached execution passed (17 controller model calls),
including two workers, complete combined checks, independent review, patch
application check and reconnect. Final reports:
`/tmp/shinobi-workflow-evaluation-mc4cw04w/evaluation.json` and
`/tmp/shinobi-execution-pi-q0s3t4ck/report.json`.

Both final targets initially encountered provider HTTP 504 before their first
turn could complete. One bounded recheck passed; no provider routing or automatic
retry policy was changed. Earlier failed, incomplete and amendment outcomes
remain visible in the JSON snapshot. Successful later acceptance does not erase
them or establish a production reliability rate. The full six-case live run was
5/6 before subsequent handoff/schema fixes, followed by targeted diagnostic and
Pi validation under the final controller. This is not a complete repeated
configuration comparison or a claim of six first-attempt successes.

```bash
export SHINOBI_MODEL=deepseek/deepseek-v4.1-flash
# OPENROUTER_API_KEY is supplied through the environment, never the command.
npm exec -- nx run shinobi-agent:smoke-live
npm exec -- nx run shinobi-agent:smoke-execution-live
npm exec -- nx run shinobi-agent:evaluate-live
npm exec -- nx run shinobi-agent:evaluate \
  --args='--live --repeats=1 --workers=1 --cases=read-only-diagnosis'
```

## Limits and remaining release work

The corpus is a small original stdlib fixture suite, not a broad repository
benchmark. Hidden judges assess executable behavior, structure and source
preservation; narrative explanations still rely on model assurance. Provider
cost and human intervention remain unknown. Coordinator/controller calls include
failed attempts; execution token observations are separate from unmeasured
coordinator tokens.

The profile measures selected installed executables, backend versions and trusted
controller files; it is not a hermetic image of every library/runtime byte.
Resource limits remain per process, without aggregate cgroup memory/PID quotas.
Dependencies are not installed, dirty source is not included, external guidance
or Pi packages are not imported, and steering still invalidates the whole run.

Broad repository quality, repeated live cost/throughput comparisons, optional
third-party integrations, selective steering and S6 are open in the
[roadmap](../../docs/agent-development/DEVELOPMENT_SLICES.md). Old approvals need
new review under schema 2/policy `local-bwrap-v2`.
