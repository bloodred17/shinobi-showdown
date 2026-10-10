# Pi → Python Deep Agent POC

This experiment routes ordinary typed Pi input through one local TypeScript
extension to a fresh Python process running `create_deep_agent`. Each request gets
a new agent and a retained `/tmp/shinobi-deepagent-*` workspace. The runner seeds
only `input.txt`; the agent must create `result.txt` itself.

Pinned dependencies: Pi **0.84.4**, Deep Agents **0.7.23**,
`langchain-openrouter` **0.2.9**, OpenRouter SDK **0.11.46**, TypeScript **6.0.3**.
Use Node 24.15–26, npm 12.0.2, Python 3.12, and uv. Both dependency graphs have local
lockfiles. Deep Agents installs Anthropic and Google integrations transitively;
this runner only constructs the explicitly configured OpenRouter model.

## Setup and run

From the repository root:

```bash
npm ci
npm exec -- nx run pi-deepagent-poc:setup
```

Provide `OPENROUTER_API_KEY` through your environment. Set `SHINOBI_POC_MODEL` to an
explicit, currently available OpenRouter `vendor/model` ID supporting tool calls.
There is no default model. OpenAI, Anthropic, and `openrouter/*` routing IDs are
rejected; choose a concrete model from another family. Check the live
[OpenRouter model catalogue](https://openrouter.ai/models) before selecting it.
Unknown models fail through the provider; there is no model fallback.

```bash
export SHINOBI_POC_MODEL='your-vendor/your-tool-capable-model'
npm exec -- nx run pi-deepagent-poc:serve --output-style=stream-without-prefixes
```

`serve` starts the pinned local Pi with a fresh profile under `/tmp`, disables
discovery of other extensions, skills, templates, and context files, and loads
only this extension. Pi's own tools are disabled. The backend API key stays in the
environment and is never written to the scratch directory. `SHINOBI_POC_PYTHON`
can override the executable; the default is this project's `.venv/bin/python`.
Use the streaming output style above so Pi's TUI is shown immediately without Nx
prefixes or its own terminal UI taking over input.

Type:

```text
What is 17 + 25? Reply with the number only.
```

Then:

```text
Read /input.txt. Write /result.txt containing the unique non-empty lines sorted alphabetically, one per line. Read the result back and tell me how many lines it contains.
```

Expected file content is `apple`, `banana`, `pear`, one per line, and the answer
reports three lines. Inspect the actual workspace path displayed in Pi. For the
changed fixture, restart with `SHINOBI_POC_FIXTURE=changed`, repeat the same query,
and expect `kiwi`, `zebra`, and two lines.

## Verification

```bash
npm exec -- nx run pi-deepagent-poc:typecheck
npm exec -- nx run pi-deepagent-poc:lint
npm exec -- nx run pi-deepagent-poc:format-check
npm exec -- nx run pi-deepagent-poc:test
npm exec -- nx run pi-deepagent-poc:smoke-live
```

The `test` target runs bridge tests, offline Python configuration/filesystem tests,
and a real Pi TUI driven through a PTY with a controlled fake child. It checks
ordinary interactive input, visible results, malformed-result recovery, busy
rejection, and zero native inference calls. An additional Pi session runs without
the bridge as a negative control: the same fail-on-call provider must record a
native call, demonstrating that the guard is active. The fake run has no provider
credentials and is **not real-model evidence**.

`smoke-live` requires the model and key. It first invokes the real backend
directly, then drives the arithmetic query and both fixture variants through the
actual Pi TUI. It checks callback tool inputs/results, input read → result write →
result readback ordering, independent host file contents, displayed workspace,
fresh request workspaces, and zero Pi-native inference calls. Logs, transcript
records, sanitized TUI output, and `report.json` are retained in the reported
`/tmp/shinobi-pi-smoke-*` directory. Missing configuration exits with code 2 and
verdict `blocked`; it never marks the POC proven.

In a restricted agent sandbox, Nx may need `NX_DAEMON=false
NX_ISOLATE_PLUGINS=false`. If its native command runner cannot create PTYs, use
`NX_NATIVE_COMMAND_RUNNER=false` for noninteractive tasks. The Pi smoke tests
themselves require PTY access. Dependency setup and live model calls also require
network access.

## Contract and limits

- One UTF-8 JSON request plus newline on stdin, then EOF:
  `{"request_id":"poc-001","query":"Read /input.txt ..."}`.
- One final JSON object plus newline on stdout, with `request_id`, `status`,
  `answer`, configured `model`, actual `workspace`, and callback-derived
  `tool_calls`. The runner also reports `model_calls` and `bound_tools`.
- Controlled errors include a short sanitized `error` and exit nonzero.
  Diagnostics use stderr. The bridge validates the response ID, schema, and exit
  status, and displays failures without falling through to Pi inference.
- One request at a time, no queue. Attachments and empty queries are rejected.
  The input hook returns `handled` immediately; the child runs in the background.
- Wall timeout: **120 seconds**, enforced by both bridge and runner. Graph
  recursion limit: **30**. OpenRouter HTTP operation timeout: **60 seconds**;
  model output limit: **4096 tokens per model call**. These are not a dollar cap.
- No custom retries. Both integration and underlying OpenRouter SDK retries are
  explicitly disabled. `langchain-openrouter` 0.2.9's `max_retries=0` alone leaves
  the SDK's default backoff enabled, so the supplied SDK client also sets
  `retry_config=None`. Provider fallback is disabled and tool-parameter support
  is required.
- Input cap **64 KiB**; captured stdout **256 KiB**, stderr **64 KiB**. Excess
  output stops the child. SIGTERM is followed by SIGKILL after one second if
  necessary. Session shutdown terminates the owned child and suppresses late
  output. Timeout/cancellation leaves any scratch work unverified.

Deep Agents' public profile API disables the automatically added general-purpose
delegate; an empty custom-subagent list alone does not do this. No skill or memory
sources are supplied. The todo and execute tools are hidden from model exposure.
The filesystem dispatch node still contains a nonfunctional execute stub; the
backend implements no shell execution. Offline tests check the actual tools bound
to the model after middleware, rather than treating that dispatch list as the
exposed tool list.

`FilesystemBackend(root_dir=scratch, virtual_mode=True)` performs real local file
operations and rejects parent traversal and symlinks escaping that root. A tilde
is a literal directory within the virtual filesystem. This is a file-tool
restriction, **not operating-system isolation**. Internal Deep Agents artifacts
may also appear in scratch. Scratch directories are retained for inspection;
delete only the specific directories you no longer need.

This POC has no conversation continuity, recovery, shell/network tools, Git
operations, custom orchestration, approval UI, or deployment. It does not establish
autonomous coding reliability or production isolation. See [EVIDENCE.md](EVIDENCE.md)
for the observed verdict and remaining checks.
