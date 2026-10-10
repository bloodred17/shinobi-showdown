# POC evidence — 2026-10-10

Verdict: **proven** for this local integration slice. The actual Pi TUI → extension
→ Python subprocess → real Deep Agent/model → file tools → visible response path
passes with `deepseek/deepseek-v4.1-flash`. Both fixture variants have independently
checked host files and successful read → write → readback execution records.

Configuration was initially unavailable. After the user supplied both variables
through the inherited environment, the live target passed on 2026-10-10 in 28.6
seconds. The API key is not recorded in this report or the scratch directories.

## Runtime and dependency pins

| Component               | Observed version/configuration                     |
| ----------------------- | -------------------------------------------------- |
| Node                    | 26.7.0                                             |
| npm                     | 12.0.2                                             |
| Nx                      | 23.3.0                                             |
| Pi                      | 0.84.4, installed locally in the POC               |
| Python                  | 3.12.3, project-local virtual environment          |
| uv                      | 0.11.1                                             |
| Deep Agents             | 0.7.23                                             |
| LangChain               | 1.4.4                                              |
| LangGraph               | 1.2.14                                             |
| `langchain-openrouter`  | 0.2.9                                              |
| OpenRouter SDK          | 0.11.46                                            |
| TypeScript              | 6.0.3                                              |
| Real model ID           | `deepseek/deepseek-v4.1-flash`; no default         |
| Fake bridge model label | `fake-test-only`; not a real model                 |
| Pi test provider        | `poc-guard/fail-on-call`; cannot perform inference |

All npm/Python dependencies are locked under this project. The workspace root
dependency files and game/web application sources have no tracked diff.

## Passed checks

- Eight TypeScript tests cover literal JSON transport, launch failure, empty or
  malformed output, request-ID/schema/exit-code checks, error redaction, bounded
  output, timeout, cancellation, busy rejection, recovery, and shutdown cleanup.
- Five Python tests cover required configuration, excluded model families,
  nonzero controlled-error responses, real filesystem writes/reads, parent and
  symlink escape rejection, actual compiled Deep Agent construction, tools exposed
  after middleware, and callback evidence from actual Deep Agent file-tool
  execution with model generation patched offline.
- For the agent tool-exposure check, model generation is patched offline. Actual
  bound tools include file tools and exclude `task`, `execute`, and `write_todos`.
  This is a configuration test, not a live model invocation. No skills or memory
  sources are supplied.
- TypeScript typecheck, scoped ESLint, and formatting checks pass.
- The documented Nx setup target passes against both local lockfiles. The Nx
  serve target launches the actual Pi TUI with no usable Pi inference credentials;
  ordinary input reaches the real runner and displays its missing-model error.
- A real Pi 0.84.4 interactive TUI is driven through a PTY with no usable provider
  credentials. The test child receives the actual typed query unchanged, and Pi
  renders the returned answer, workspace label, and request ID.
- The TUI remains usable after malformed JSON and rejects a concurrent input.
  Handled input records zero native model calls. The same selected fail-on-call
  provider, in a separate Pi session without the bridge, records one native call.

The passing TUI run is retained at
[/tmp/shinobi-pi-smoke-q404cyqh/report.json](/tmp/shinobi-pi-smoke-q404cyqh/report.json).
Its [transcript and guard records](/tmp/shinobi-pi-smoke-q404cyqh/default/guard.jsonl),
[sanitized terminal output](/tmp/shinobi-pi-smoke-q404cyqh/default/tui.txt), and
[negative control](/tmp/shinobi-pi-smoke-q404cyqh/control/guard.jsonl) are available
on this host. These paths are test artifacts, not portable fixtures.

The query was:

```text
What is 17 + 25? Reply with the number only.
```

The actual displayed response was:

```text
42

Workspace: /tmp/fake-test-only
Model: fake-test-only
Tools: none
Request: 3920eb47-5ef9-49e4-9bf0-8236a9f52abb
```

`/tmp/fake-test-only` is deliberately a fake label; this run proves neither file
work nor real Deep Agents/model execution. The test evidence also contains the
malformed-output error, subsequent recovery response, visible busy error, and
successful completion of the first concurrent request.

Pi 0.84.4 defers disk session creation until a native assistant message. The test
guard therefore captures public in-memory session entries using a test-only
command; it also independently checks captured terminal output. It does not force
a native turn merely to create a session file.

## Live model evidence

With both configuration variables inherited from the environment, this command
passed without changing the model, runner, bridge, or tests:

```bash
npm exec -- nx run pi-deepagent-poc:smoke-live --output-style=static
```

The passing [live report](/tmp/shinobi-pi-smoke-hglw6497/report.json) is retained
with the [direct backend result](/tmp/shinobi-pi-smoke-hglw6497/direct.json),
[default Pi transcript/guard](/tmp/shinobi-pi-smoke-hglw6497/default/guard.jsonl),
[changed Pi transcript/guard](/tmp/shinobi-pi-smoke-hglw6497/changed/guard.jsonl),
and sanitized terminal captures under the same evidence directory. These are
host-local test artifacts, not portable fixtures.

The arithmetic query above produced `42` in Pi, with one model invocation and no
tool calls. Its workspace was `/tmp/shinobi-deepagent-i_ancw0e`; its request ID was
`c6046f40-d606-469d-a20a-a3420e6dea2c`.

The exact ordinary typed file query, unchanged for both fixtures, was:

```text
Read /input.txt. Write /result.txt containing the unique non-empty lines sorted alphabetically, one per line. Read the result back and tell me how many lines it contains.
```

| Run                | Retained result file                                                                     | Independently checked content | Pi answer      |
| ------------------ | ---------------------------------------------------------------------------------------- | ----------------------------- | -------------- |
| Direct backend     | [/tmp/shinobi-deepagent-6mbde849/result.txt](/tmp/shinobi-deepagent-6mbde849/result.txt) | `apple\nbanana\npear\n`       | Not a Pi query |
| Pi default fixture | [/tmp/shinobi-deepagent-3bl_c0n2/result.txt](/tmp/shinobi-deepagent-3bl_c0n2/result.txt) | `apple\nbanana\npear\n`       | 3 lines        |
| Pi changed fixture | [/tmp/shinobi-deepagent-etm381ee/result.txt](/tmp/shinobi-deepagent-etm381ee/result.txt) | `kiwi\nzebra\n`               | 2 lines        |

The Pi file-task request IDs were `9c711fc2-7a93-4016-a61e-46bc4f384284` and
`691191bd-4868-4791-b647-08f2d136926d`. Each recorded four invocations of the
configured model and these actual successful tool calls, in order:

1. `read_file` with `file_path: /input.txt` returned the seeded fixture.
2. `write_file` with `file_path: /result.txt` wrote the sorted unique lines.
3. `read_file` with `file_path: /result.txt` returned the written result.

The terminal captures and public session entries show the final answers, actual
scratch paths, configured model ID, successful tool summary, and request IDs.
The tests check displayed request/path text as well as the session entries.
Host-side inspection independently confirmed the exact fixture and result bytes.

Actual model-bound tools were `ls`, `read_file`, `write_file`, `edit_file`,
`delete`, `glob`, and `grep`; `task`, `execute`, and `write_todos` were absent.
No delegation calls occurred, and no skills or memory sources were supplied.
Each query used a fresh process, agent, and scratch workspace.

Both live Pi sessions recorded **zero native model calls** and a zero-call guard
proof. The separate [negative control](/tmp/shinobi-pi-smoke-hglw6497/control/guard.jsonl),
with the same selected fail-on-call provider but without the bridge, recorded
**one native call**. The earlier fake-child TUI run additionally passed with no
usable provider credentials. The live Pi session uses the fail-on-call test
provider; the real backend alone performs the configured model task.

Missing-configuration preflight errors were observed before this live run.
Unavailable-model provider errors remain untested; they are not needed to claim
the observed successful configured-model path.

All 13 focused tests and the credential-free fake-child TUI check were rerun
successfully after the live run. That additional
[bridge-only report](/tmp/shinobi-pi-smoke-gxb06gy2/report.json) deliberately reports
`partially proven` for its fake-only mode; the real-model verdict is established
by the separate passing live report above.

## Limits of the result

This proves the local bridge, real Deep Agent file tasks through Pi, and selected
failure behavior. It does not prove autonomous coding reliability, production
isolation, conversation continuity, restart recovery, or deployment readiness.

The filesystem test verifies local tool-path restrictions, not OS isolation.
Deep Agents' internal artifacts may share the disposable scratch directory. The
underlying OpenRouter SDK's retries are explicitly disabled as well as the model
integration's retries; the bridge and runner both enforce a 120-second deadline.
