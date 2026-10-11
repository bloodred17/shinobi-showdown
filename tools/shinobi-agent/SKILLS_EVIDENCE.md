# Shinobi-owned skill validation

Recorded 2026-10-11 against the working tree on Git baseline `05cedb15170888e5682b8a00623e4daf09feca07`.
This is an uncommitted implementation snapshot, not a claim that the baseline
commit contains these changes. The sorted relative-path/SHA-256 manifest of local
skill files, top-level Python/TypeScript runtime files and Python/TypeScript tests
has aggregate SHA-256 `2dfd89538afe3ae880c34d9b7568a396eaa457ac0ec82e4ef4c30876a3c9a0f5` (170 files; canonical JSON with sorted keys and compact separators).

## Results

| Check                                    | Observed result                                                                                                                                        |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Skill creator structural validation      | All 44 skill entrypoints passed                                                                                                                        |
| Local catalogue/resources                | All registered procedures and local Markdown links load without network access                                                                         |
| Local ownership regression               | A local reference edit is accepted by a new workflow without changing historical attribution; an earlier bound reader rejects the changed resource     |
| Selection regression                     | Investigation/refactor omit TDD; discovery includes its local dependencies; multi-item work selects dependency execution; maintenance remains optional |
| Authority regression                     | Unselected resources and traversal rejected; autonomy still needs a new exact contract; switching it off removes its procedure                         |
| Python regression                        | 88 tests passed                                                                                                                                        |
| Bridge regression                        | 11 tests passed                                                                                                                                        |
| Scripted Pi conversation integration     | Passed, real runtime with scripted model output                                                                                                        |
| Scripted Pi detached execution/reconnect | Passed, real controller and Bubblewrap with scripted model output                                                                                      |
| Typecheck, lint, format-check            | Passed through Nx                                                                                                                                      |
| Whitespace validation                    | `git diff --check` passed                                                                                                                              |

Commands:

```bash
npm exec -- nx run shinobi-agent:test --output-style=stream
npm exec -- nx run-many -t typecheck lint format-check -p shinobi-agent --output-style=stream
```

Nx ran with its daemon/plugin isolation disabled and an isolated writable
`NX_WORKSPACE_DATA_DIRECTORY` under `/tmp`. The first sandboxed runtime attempt
was blocked by the outer sandbox's NETLINK_ROUTE restriction; the successful
rerun used host permissions to exercise Shinobi's own Bubblewrap sandbox. The
first host run exposed an obsolete expectation that autonomy did not change the
skill selection; the corrected test now checks the added/removed local procedure
and preserves the unchanged scope, checks, budgets and explicit approval assertions.
The subsequent complete run passed.

Raw session logs: `/tmp/shinobi-owned-skills-tests.log`. Pi reports:
`/tmp/shinobi-session-smoke-awpx3w4v/report.json` and
`/tmp/shinobi-execution-pi-rme0iotb/report.json`. These temporary paths may expire;
the results above are the retained summary.

## Limits

No live provider evaluation or baseline/candidate skill-quality comparison ran
for this revision. Structural and scripted checks do not prove that a model will
choose the right skill, follow it faithfully or produce better software. The
historical 0/7 live lifecycle result remains recorded separately. Browser/service
verification, external publication and new execution profiles were not added.
