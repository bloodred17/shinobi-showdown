# Local slices 1–3 validation — 2026-10-10

Verdict: **implemented and validated on small local acceptance repositories**.
Both continuing conversations and approved execution passed through the actual
Pi TUI with real Deep Agents using `deepseek/deepseek-v4.1-flash`.
This establishes the observed local paths and gates; broad autonomous coding
quality and real-task parallel cost/throughput improvements remain unevaluated.

## Final checks

The combined regression command passed all eight targets:

```bash
NX_DAEMON=false NX_ISOLATE_PLUGINS=false NX_NATIVE_COMMAND_RUNNER=false \
NX_WORKSPACE_DATA_DIRECTORY=/tmp/shinobi-nx-final \
npm exec -- nx run-many -t test typecheck lint format-check \
  -p shinobi-agent pi-deepagent-poc --output-style=static
```

After the exact-byte Git and source-inspection guards, shinobi-agent:test passed
again with all 29 Python tests, six bridge tests and both actual Pi smoke checks.

- Shinobi: six TypeScript bridge tests and 29 Python runtime/execution tests.
- Actual Pi TUI tests use the real extension, subprocess transport, Deep Agents
  graph, SQLite state, Bubblewrap file tools, controller and independent checks.
  Only model generation is scripted in offline runs.
- Tests cover explicit/stale/duplicate approval, cycles and missing dependencies,
  ownership violations, serialized overlap, dependency ordering, two-worker
  integration, selective repair retaining unaffected work, repair exhaustion,
  missing assurance coverage, call-budget exhaustion and stale artifacts.
  The final focused run also checks exact Git bytes, tracked ignored files,
  binary content, executable modes and patch application without filters.
- Git inspection disables repository fsmonitor and hooks; its regression check
  confirms that snapshot creation does not execute a configured fsmonitor hook.
- Bubblewrap tests establish read-only command access, network denial, absent
  provider credentials, path traversal/symlink rejection and fail-closed preflight.
- Active cancellation settles workers without subsequent writes. A detached
  controller killed during a model call becomes interrupted; explicit recovery
  reconciles the existing attempts and reaches verified under unchanged approval.
  Steering invalidates old proposals even if no replacement proposal exists yet.
- TypeScript typecheck, scoped ESLint and formatting pass.
- The unchanged POC passes its eight TypeScript and five Python tests plus actual
  Pi bridge smoke, typecheck, lint and formatting checks. Its historical real-model
  evidence is preserved in tools/pi-deepagent-poc/EVIDENCE.md.

Final offline reports:

- [Conversation](/tmp/shinobi-session-smoke-zv5qkwh0/report.json)
- [Approved execution](/tmp/shinobi-execution-pi-kf3eyxqx/report.json)
- [POC bridge regression](/tmp/shinobi-pi-smoke-rly3axp2/report.json)

The POC regression is fake-backend bridge evidence, not a rerun of its historical
live task. No restricted-environment failure was counted as a successful check.

## Live conversation path

```bash
SHINOBI_MODEL=deepseek/deepseek-v4.1-flash \
NX_DAEMON=false NX_ISOLATE_PLUGINS=false NX_NATIVE_COMMAND_RUNNER=false \
NX_WORKSPACE_DATA_DIRECTORY=/tmp/shinobi-nx-slice1-live \
npm exec -- nx run shinobi-agent:smoke-live --output-style=static
```

Passed in 48.2 seconds. The [live report](/tmp/shinobi-session-smoke-b6udhamz/report.json)
records a repository-grounded retry-cap proposal, constraint revision from 10 to
20, restart/resume retaining the latest constraint, refusal to write through chat,
unchanged source/snapshot files and zero Pi-native inference. A separate negative
control invokes the selected fail-on-call Pi provider.

This supersedes the earlier Slice 1 report's missing-model blocker.

## Live approved execution path

```bash
SHINOBI_MODEL=deepseek/deepseek-v4.1-flash \
NX_DAEMON=false NX_ISOLATE_PLUGINS=false NX_NATIVE_COMMAND_RUNNER=false \
NX_WORKSPACE_DATA_DIRECTORY=/tmp/shinobi-nx-execution-live \
npm exec -- nx run shinobi-agent:smoke-execution-live --output-style=static
```

Passed in 55.7 seconds on the final exact-byte Git implementation. The [live report](/tmp/shinobi-execution-pi-70ghxwkn/report.json)
contains the exact query, proposal, approved contract, worker tool execution,
independent check outputs, assurance coverage and artifact identity.

Observed behavior:

1. Actual typed input asks for a retry-delay cap of 10 and TIMEOUT of 20, preserving
   the public API and restricting writes to reconnect.py and limits.py.
2. Pi presents the source-grounded proposal and executable contract. Before the
   explicit hash approval, no approval record exists and repository files remain
   unchanged.
3. Actual typed `/shinobi-approve <hash>` creates one durable approved run.
   Its state was queued when Pi closed.
4. Two real Deep Agents run in separate repository copies. Each records source
   reads, a successful replace_source call and an advisory approved check.
   Credentials/model coordination stay outside the repository sandbox.
5. Their changes integrate sequentially. The combined independent behavior check
   exits zero with two tests passing. The public function signature and
   retry_delay(0) behavior remain unchanged.
6. A fresh read-only reviewer returns pass with coverage for all four acceptance
   criteria. Its evidence hash matches the checked artifact.
7. The controller finishes while Pi is closed. Restarting Pi and resuming the
   session displays the verified deliverable.
8. Host inspection confirms the resulting constants, unchanged user repository,
   matching content hash and a patch that passes git apply --check.
9. Both Pi sessions record zero native model calls; the separate negative control
   records a native call. The run uses 13 backend model calls.

The synthetic local result commit is
`9dda22cab150f8c7602a604f3697fb1639119659`, based on original fixture source commit
`b6ccc1214f84b6c6b7130434d3bdb47c592d877c`.

- [Result patch](/tmp/shinobi-execution-pi-70ghxwkn/state/runs/1050418687b2450c9e7be4fd85bf7633/result.patch)
- [Standalone evidence](/tmp/shinobi-execution-pi-70ghxwkn/state/runs/1050418687b2450c9e7be4fd85bf7633/evidence.json)

The verified content hash is
`41d4b6394fbb74aed9a75e6215fc470fcc8f6d732e08c948b5dc0eff82e1e2b7`.
The patch hash is
`6fc49d092f66f756fbafc300b1d58e7ae7ddba4f3082fba4989e2e948ca833a5`.
These are retained host-local test artifacts.

## Runtime and limits

| Component                             | Version/configuration        |
| ------------------------------------- | ---------------------------- |
| Node / npm                            | 26.7.0 / 12.0.2              |
| Nx                                    | 23.3.0                       |
| Pi                                    | 0.84.4                       |
| Backend Python                        | 3.12.13                      |
| Deep Agents                           | 0.7.23                       |
| LangChain / langchain-core            | 1.4.4 / 1.6.9                |
| LangGraph                             | 1.2.14                       |
| SQLite checkpoint package             | 3.1.1                        |
| langchain-openrouter / OpenRouter SDK | 0.2.9 / 0.11.46              |
| Live model                            | deepseek/deepseek-v4.1-flash |

Dependencies remain project-local and locked; no new external package was needed.
The test invocation explicitly configures SHINOBI_MODEL. Production still has no
model default or implicit reuse of SHINOBI_POC_MODEL.

Initial restricted Bubblewrap preflight failed because Codex blocked namespaces;
the same check and subsequent tests passed with the required access. One Nx
invocation segfaulted before starting its target; retrying with an isolated
workspace data directory succeeded. No provider task was executed by that failed
invocation. Existing Nx Vite plugin deprecation warnings were unchanged.

The local sandbox supplies namespace, mount and egress isolation plus per-process
limits, not a production aggregate cgroup memory/PID quota. Verification uses
offline system tools with no host dependency mounts or network installation.
Repositories needing other dependencies require a separately reviewed execution
environment. Large repositories, symlinks and submodules remain unsupported.

Parallel scheduling and correctness are observed; useful throughput or cost
improvement on realistic tasks has not been benchmarked. Independent assurance is
a model recommendation backed by checks, not proof of every semantic requirement.
Steering conservatively pauses the whole run. Paused time counts toward its
wall-clock budget. No automatic publishing, GitHub integration, VPC provisioning,
CI deployment, staging or merge was added.

Product code changes are under tools/shinobi-agent. Application sources, workspace
dependency files and the existing POC were preserved. The repository code graph
was refreshed as required by the inherited AGENTS.md instructions.
