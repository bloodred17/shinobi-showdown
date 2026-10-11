# Local lifecycle validation — 2026-10-11

The requirements-grounded lifecycle passed the local regression suite and repeated
scripted evaluation. This establishes controller behavior on the supported local
profile. At this checkpoint, live evaluation awaited a restarted environment.
The subsequent [live evaluation](LIFECYCLE_LIVE_EVIDENCE.md) completed 0/7 corpus
cases while the separate live Pi integration check passed; those results limit
the conclusions that can be drawn from this scripted evidence.

The tested checkout contains uncommitted approved changes over
`05cedb15170888e5682b8a00623e4daf09feca07`. The baseline commit alone does not identify
this implementation. [The captured evaluation](LIFECYCLE_EVIDENCE.json) records
runtime file hashes, the harness hash, workflow and skill-resource fingerprints,
corpus hash, configuration and every trial. These fingerprints were checked
against the final runtime after evaluation.

## Results

| Check                                             | Result                                                                  | Evidence scope                                                                                         |
| ------------------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `shinobi-agent:test`                              | 84 Python tests and 11 bridge tests passed; both Pi smoke checks passed | Real controller, filesystem, SQLite, Bubblewrap, subprocess and Pi execution; scripted model responses |
| `shinobi-agent:evaluate`                          | 42/42 independently correct trials                                      | Seven cases, three repetitions, one and two workers                                                    |
| Evaluation boundary checks                        | Zero observed false successes or unauthorized actions                   | Fixture judge, source preservation and declared write-scope checks                                     |
| `shinobi-agent:typecheck`, `lint`, `format-check` | Passed                                                                  | TypeScript, configured lint and formatting targets                                                     |
| Skill package validation                          | 15/15 passed                                                            | Skill-creator frontmatter validation; selected upstream resource hashes also validated by the runtime  |

Regression coverage includes rejected planning without a contract, fabricated
requirement origins, missing coverage, requirement revision/removal rules,
final-validation rejection after a quality pass, optional adversarial rejection,
new tests failing before admission and passing after implementation, admitted-test
tampering, bounded correction, approval, pause/recovery and detached execution.

The new CLI case launches the public command and checks both its stdout and its
written receipt. The corpus also covers library fixes, a feature, a refactor,
read-only investigation and dependent/independent work. The scripted reviewers
exercise gate handling; they do not establish that a live model identifies all
semantic defects.

During validation, a correction event attempted to serialize a set of affected
items; it now records a sorted list. The cost-accounting test was updated to derive
sample count from the expanded corpus. The planning-rejection transport fixture
was corrected to use the contract operation. The complete final suite passed
after these corrections.

## Reproduction and retained local evidence

Run through the workspace package manager:

```bash
npm exec -- nx run shinobi-agent:test
npm exec -- nx run shinobi-agent:evaluate
npm exec -- nx run-many -t typecheck lint format-check -p shinobi-agent
```

This session disabled the Nx daemon/plugin isolation/native command runner and
used separate `NX_WORKSPACE_DATA_DIRECTORY` directories under `/tmp`. Real
Bubblewrap tests ran with host namespace access; the runtime did not fall back to
unsandboxed repository execution.

Additional session-local evidence is retained at:

- `/tmp/shinobi-lifecycle-final-test3.log`
- `/tmp/shinobi-session-smoke-rzqm8f12/report.json`
- `/tmp/shinobi-execution-pi-5i0_it9p/report.json`
- `/tmp/shinobi-workflow-evaluation-clb4l4et/` (per-trial state, checks and judges)

Installed versions checked for this run: Deep Agents 0.7.23, LangGraph 1.2.14,
langchain-openrouter 0.2.9 and langgraph-checkpoint-sqlite 3.1.1.

## Limits

At the scripted checkpoint, the Codex process and a fresh login shell could see the provider key's
presence but not `SHINOBI_MODEL`; no key value was displayed, no model was inferred,
and no live result was claimed. After restart, both live targets ran; see the
[separate live report](LIFECYCLE_LIVE_EVIDENCE.md) for results and retained failures.

The evaluation compares worker counts within this implementation. It does not
compare the historical three-skill runtime against this lifecycle, establish
broad model reliability, or validate an Angular/Rust/browser/service environment.
Model cost and human interventions remain unknown. The evaluation correctly
declined automatic adoption and did not establish a predeclared speed/cost gain.
Exact-contract approval and existing local-only execution boundaries remain.
