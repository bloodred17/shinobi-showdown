# Shinobi — approved local repository engineering

The Pi extension connects continuing conversations to an independent Python Deep
Agents/LangGraph backend. Slice 1 investigates committed source and proposes work.
Slice 2 completes an explicitly approved contract with one implementer, OS
isolation, durable control, verification, independent review, and bounded repairs.
Slice 3 adds two-worker scheduling, ownership and dependency validation, serialized
integration, and selective repairs.

## Start

Use Linux with Bubblewrap, util-linux `prlimit`, system Python 3.12 and Git.
The interface/backend dependencies remain pinned locally: Node 24.15–26,
npm 12.0.2, Python 3.12, uv, Pi 0.84.4 and Deep Agents 0.7.23.

```bash
npm exec -- nx run shinobi-agent:setup
export SHINOBI_MODEL='your-vendor/your-tool-capable-model'
export SHINOBI_REPOSITORY='/absolute/path/to/repository'
# Supply OPENROUTER_API_KEY through the environment.
npm exec -- nx run shinobi-agent:serve --output-style=stream-without-prefixes
```

Configure a concrete tool-capable OpenRouter model. OpenAI, Anthropic and automatic
routing are excluded. There is no model default, fallback, SDK retry, or
production fake-model mode. Ambient LangSmith tracing is disabled.

## Propose, review, approve

Describe the behavior and constraints in ordinary Pi input. Shinobi reads the
selected committed source, asks material questions and drafts a versioned proposal.
Ask it to include verification commands and bounded work assignments. A chat
response cannot authorize execution.

Type `/shinobi-contract` to turn the latest proposal into a reviewable execution
contract. Missing checks, unresolved questions, unknown dependencies, dependency
cycles or ownership outside the proposal are rejected. If you need to supply the
execution settings explicitly, append a JSON object to that command:

```json
{
  "checks": [
    {
      "id": "behavior",
      "argv": ["python3.12", "-B", "-m", "unittest", "test_behavior"],
      "cwd": ".",
      "timeout_seconds": 60,
      "affected_items": ["cap"]
    }
  ],
  "work_items": [
    {
      "id": "cap",
      "instruction": "Cap retry_delay at 10 while preserving its signature.",
      "paths": ["reconnect.py"],
      "depends_on": []
    }
  ],
  "limits": {
    "max_workers": 1,
    "repair_cycles": 2,
    "replans": 1,
    "wall_seconds": 900,
    "model_calls": 60,
    "graph_steps": 30
  }
}
```

Review the displayed behavior, constraints, exclusions, paths, commands, work
assignments, limits, model, policy and source commit. Then type
`/shinobi-approve <displayed-contract-hash>`. This exact input is the approval
operation. The immutable hash binds every contract field. Repeated delivery of
the same approval cannot create another run. Changed proposals, policies, models,
or source HEAD require another review and approval.

Writable scope uses explicit repository-relative files or directory prefixes
ending in `/`; no glob patterns, traversal, Git metadata, dependency trees or
backend state. Work assignments must cover the proposal's affected paths.
Allow test-file changes explicitly when new tests are part of the requested work.

## Controls and reconnect

| Command                             | Behavior                                                                         |
| ----------------------------------- | -------------------------------------------------------------------------------- |
| `/shinobi-new /absolute/repository` | Start a conversation at SHINOBI_REVISION, default HEAD.                          |
| `/shinobi-resume <session-id>`      | Restore conversation, current contract and run; reconnect to progress.           |
| `/shinobi-session`                  | Show the current conversation and reconnect to its run.                          |
| `/shinobi-sessions`                 | List the latest 50 conversations.                                                |
| `/shinobi-contract [settings JSON]` | Review an executable contract; creates no approval.                              |
| `/shinobi-approve <hash>`           | Approve the exact latest contract and start detached execution.                  |
| `/shinobi-status`                   | Inspect durable state, checks, review and local deliverable.                     |
| `/shinobi-pause`                    | Stop dispatch and settle active operations, then become paused.                  |
| `/shinobi-continue`                 | Explicitly continue a settled paused run under unchanged authority.              |
| `/shinobi-cancel`                   | Stop and preserve partial files; becomes cancelled after operations settle.      |
| `/shinobi-steer <instruction>`      | Record direction, stop affected execution and invalidate old authority.          |
| `/shinobi-recover`                  | Reconcile and explicitly recover an interrupted controller within its allowance. |

New direction during an unfinished run, including ordinary chat, conservatively
pauses the entire run and invalidates its proposal. Recorded steering is supplied
to the next coordinator turn even if an earlier model call failed. Ask for a
revised proposal, review the replacement contract, and approve it before further
writes. Use the status command for progress without changing direction.

Closing Pi aborts its current conversation/control transport, but an approved
execution controller lives independently in a detached process. Resume the
backend session after restarting Pi. Polling displays durable progress and never
starts Pi-native inference. Native Pi new/resume/fork changes the backend selection.
An active adapter request blocks native session switching; an independent run
continues when the adapter changes sessions.

Pausing and cancellation acknowledge an intermediate state while already active
operations settle. Sandbox commands are stopped promptly; a provider call may take
up to its 60-second timeout. No further tools or dispatch are admitted afterward.
No destructive rollback or cleanup of partial implementation is implied.

## Source and workspace isolation

Conversation discovery exports regular UTF-8 Git blobs into a read-only session
snapshot. It excludes binary files, symlinks, submodules and files over 1 MiB.
Citations require valid lines that were actually read; provenance is not proof
of a model's interpretation.

Execution exports all ordinary committed blobs, including binaries and executable
modes, into an independent local Git repository. Symlinks and submodules are
unsupported and rejected. Both snapshots have a 100 MiB / 10000-file limit.
Uncommitted, staged and untracked user changes are excluded and preserved.

Each worker receives its own copy at a recorded integration baseline. Disjoint,
dependency-ready ownership can run concurrently; overlapping ownership is
serialized. At most two specialists run at once per state directory, and only one
unfinished run per source repository is permitted. Completed worker changes are
scope-checked and integrated sequentially into immutable candidate repositories.
A transactional pointer selects the accepted candidate, so an interrupted
integration does not replay a partially applied change.

Every repository file operation and verification command runs through Bubblewrap.
It isolates mount, network, PID, IPC and user namespaces, drops capabilities and
disables further user namespaces. System tools and the trusted file helper are
read-only. Provider credentials, the user's home, source checkout and backend
databases are not mounted. The process environment is cleared. Commands receive a
read-only repository and a 64 MiB writable temporary filesystem; only the trusted
file helper receives a writable worker copy and enforces ownership and safe paths.

There is no unrestricted shell tool. Workers can run only the exact approved
check IDs, using argument arrays. The reviewer has read-only source and evidence
tools. Default Deep Agents delegation, execution, writes, skills and todo workflows
are disabled; its internal state read tool may inspect ephemeral agent artifacts.

The first supported verification environment is offline Linux system tooling,
especially Python stdlib/unittest. Approved Node/npm/Git/Cargo argument arrays
can use system-installed tools and dependencies present in the committed snapshot.
No host node_modules, virtual environment, credentials, caches, dependency
installation or network fallback is supplied. A project requiring absent
dependencies cannot pass; revise its environment/contract separately.
Bubblewrap failure blocks execution instead of falling back to host execution.

## Gates, budgets and evidence

Required commands run again on the combined artifact, independently of worker
claims. Verification records retain argv, cwd, environment, exit status, output,
elapsed time and artifact hash. A fresh read-only reviewer must cover every
acceptance criterion with approved check IDs and concrete explanations. Failed
checks, missing coverage, findings or stale evidence prevent a verified result.

Checks and reviewer reports may identify affected work-item IDs for selective
repair. Their transitive dependents are also rescheduled. Other completed work is
retained. Unlocalized failures conservatively reschedule all approved items.
Every repair reruns the full combined verification and independent review.

Defaults are two repair cycles, one recovery replan, one worker, 900 seconds,
60 model calls and 30 graph steps per specialist invocation. Contracts may choose
two workers and smaller bounds; hard maxima are validated. The wall-clock budget
starts when execution begins and includes paused time. Graph steps and call counts
are protective limits, not a dollar spending cap. Commands have 1–120-second
timeouts, bounded output, per-process CPU/address-space/file-size/file-descriptor
limits. This local prototype does not impose aggregate cgroup memory or PID quotas.

Delivery provides a local branch in the run-owned Git repository, a binary-capable
patch and standalone evidence.json. The result records the original source commit,
synthetic local result commit, content hash and patch hash. The user's repository
is never automatically changed. Verified, user accepted and applied are separate;
there is no GitHub publication, cloud provisioning, staging, deployment or merge.

## State and recovery

State defaults to the ignored `tools/shinobi-agent/.state/`; SHINOBI_STATE_DIR
can select another private directory. It contains source copies, SQLite sessions,
additive approval/run/event tables, specialist/controller LangGraph checkpoints,
partial attempts, logs and artifacts. Credentials remain outside repository
sandboxes; conversation and source content in the private state directory should
be treated as project data.

Conversation attempts retain the Slice 1 isolation rules: only a validated
completed turn advances context; failed turns remain visible and are not replayed.
Execution operations bind their request ID to the complete input hash. Reusing an
ID with different input is rejected. SQLite transactions and process locks protect
authority, budgets, run ownership and integration.

After a controller dies, status marks unfinished execution interrupted without
automatically invoking the model. Explicit recovery verifies source HEAD and the
recorded integration content, marks unfinished attempts interrupted, and consumes
a replan when recovering active work. It inspects partial owned files and starts
fresh agent context rather than replaying old tool calls. Completed attempt reports
can be integrated after reconciliation. Changed baselines, external workspace
tampering, unsafe partial files or exhausted limits stop the run. Partial files
remain available for inspection; state cleanup is not automated.

Transport limits remain 120 seconds per adapter request, 64 KiB request/stderr and
256 KiB response. Sandbox output is capped at 128 KiB. File tools accept UTF-8 files
up to 1 MiB. Source code is sent to the explicitly configured model for processing.

## Validate

```bash
npm exec -- nx run shinobi-agent:format
npm exec -- nx run-many -t test typecheck lint format-check -p shinobi-agent
npm exec -- nx run shinobi-agent:smoke-live
npm exec -- nx run shinobi-agent:smoke-execution-live
```

The test target includes bridge tests, actual graph/runtime/sandbox tests and
actual Pi TUI tests driven through PTYs. Scripted models replace only generation;
production has no offline test switch. The live targets need credentials and
SHINOBI_MODEL. Both paths use a fail-on-call Pi provider plus a negative control
to establish that handled input bypasses Pi inference.

Restricted environments may require NX_DAEMON=false, NX_ISOLATE_PLUGINS=false and
NX_NATIVE_COMMAND_RUNNER=false, along with PTY/subprocess/namespace access.
If Nx's native cache crashes during project graph creation, select an isolated
NX_WORKSPACE_DATA_DIRECTORY under /tmp and rerun the same Nx target.
See EVIDENCE.md for observed checks and local reports.

Implementation map: contracts.py and execution_contracts.py define typed authority;
store.py and execution_store.py own durable state; repository.py and workspace.py
manage source copies; sandbox.py and sandbox_fileop.py enforce execution isolation;
agent.py builds roles; execution.py runs the controller; execution_api.py adapts
controls; runner.py, bridge.ts and extension.ts connect Pi.
