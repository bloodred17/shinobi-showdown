# Shinobi development slices

Date: 2026-10-10. Repository baseline inspected: `5486550`.

This is the consolidated development plan for **user-directed autonomous repository engineering**: a user supplies direction, Deep Agents work within an approved contract, and the system returns a verified result. Pi is the first interface. GitHub issues and workers in a custom VPC are the later operating model.

The user authorized creating this document and subsequently approved the bounded local S1–S5 implementation described below. That approval excludes S6 infrastructure, GitHub writes, publication and deployment. Proposed remote defaults and unresolved decisions remain identified below. Each future implementation handoff must identify its bounded, approved scope.

“No gaps” here means every required capability has an owning slice, dependencies, failure behavior, and a completion gate. It does not mean unknown infrastructure or product choices have already been decided. The decision register makes those choices explicit and prevents dependent work from being declared complete prematurely.

## Contents

- [Roadmap and current status](#roadmap-and-current-status)
- [Product boundaries and architecture](#product-boundaries-and-architecture)
- [Shared contracts and lifecycle](#shared-contracts-and-lifecycle)
- [Slice 0: Pi-to-Deep-Agent proof of concept](#slice-0-pi-to-deep-agent-proof-of-concept)
- [Slice 1: Understand and propose](#slice-1-understand-and-propose)
- [Slice 2: Approve a task](#slice-2-approve-a-task)
- [Slice 3: Implement one task](#slice-3-implement-one-task)
- [Slice 4: Verify and repair](#slice-4-verify-and-repair)
- [Slice 5: Add specialist workflows](#slice-5-add-specialist-workflows)
- [Slice 6: Run through GitHub and VPC workers](#slice-6-run-through-github-and-vpc-workers)
- [Testing and continuous improvement](#testing-and-continuous-improvement)
- [Decisions and release gates](#decisions-and-release-gates)
- [Coverage and execution order](#coverage-and-execution-order)
- [Evidence and document maintenance](#evidence-and-document-maintenance)

## Roadmap and current status

The six-slice sequence remains stable. Slice 0 records the completed POC. Historical runtime evidence used a **different, coarser three-slice numbering**. The current README follows `S0`–`S6`; do not infer missing implementation from historical numbering differences.

| Roadmap slice | User capability                                                                                      | Historical runtime numbering | Current local status after approved increment                                                                                                              |
| ------------- | ---------------------------------------------------------------------------------------------------- | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| S0            | Send a query through Pi and have a real Deep Agent perform a small task                              | Separate POC                 | Implemented; historical POC evidence retained                                                                                                              |
| S1            | Discuss a repository task, clarify it, and inspect a proposal                                        | Local slice 1                | Implemented locally, including task type and changed/preserved behavior; broader repository quality remains unevaluated                                    |
| S2            | Approve one exact executable contract                                                                | Part of local slice 2        | Schema-2 profile/workflow/oracle binding, full effective display and explicit legacy rejection implemented locally                                         |
| S3            | Execute approved work in an isolated workspace                                                       | Part of local slice 2        | Measured offline Linux profile, diagnostic read-only capability, typed blockers and recovery gates implemented                                             |
| S4            | Verify, independently review, repair within bounds, and deliver                                      | Part of local slice 2        | Protected committed oracles, baseline/final evidence, skipped/empty-suite rejection and explicit no-op disposition implemented                             |
| S5            | Select specialist workflows and coordinate larger work                                               | Local slice 3 covers part    | Four playbooks, original reviewed guidance, role models, declared semantic dependencies and versioned evaluation implemented; no default parallel adoption |
| S6            | Select a GitHub issue, run remotely, publish a verified PR, validate staging, and let the user merge | Future factory               | Planned; no working remote path established by the inspected evidence                                                                                      |

The current [runtime README](../../tools/shinobi-agent/README.md) and [evidence report](../../tools/shinobi-agent/EVIDENCE.md) describe actual Pi TUI conversation and approved execution with `deepseek/deepseek-v4.1-flash`. The report records 29 Python tests, six bridge tests, and live conversation/execution runs. These are **existing recorded results, not tests rerun while writing this plan**. They establish small local acceptance cases, not general coding quality or a demonstrated parallel efficiency gain.

Reference versions in that report include Pi 0.84.4, Deep Agents 0.7.23, Python 3.12.13, LangGraph 1.2.14, and Nx 23.3.0. They identify the observed baseline; they are not a claim about the latest upstream releases. Revalidate capabilities when versions change.

The subsequent approved local increment is recorded separately in [LOCAL_S5_EVIDENCE.md](../../tools/shinobi-agent/LOCAL_S5_EVIDENCE.md). It distinguishes current regression results, repeated scripted controller evaluation and live fixture acceptance. These additions retain the supported stdlib/system-tools boundary. S5's broader quality/cost release gate, optional external integrations, and S6 remain open.

## Product boundaries and architecture

### Intended experience

Local: **user → Pi → Shinobi extension → Python coordinator/controller → Deep Agents → isolated work → verification → local deliverable**.

Remote: **user-selected issue → authorized trigger → proposal/approval → durable queue → worker in custom VPC → local verification → PR → GitHub Actions CI → staging validation → human merge**.

The user may ask for an investigation, bug fix, feature, or refactor in ordinary language. The coordinator proposes the task type and clarifies material uncertainty. A task label alone grants no additional permissions. A refactor explicitly preserves identified behavior; a feature explicitly describes changed behavior.

The system asks again when a product choice, scope expansion, missing capability, or exhausted allowance prevents progress. Routine implementation and in-scope repairs proceed under the existing approval. It must explain what is blocked and present the smallest actionable decision.

### Ownership

| Component                             | Owns                                                                            | Does not own                                                    |
| ------------------------------------- | ------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| Pi extension / later GitHub adapter   | User input, contract rendering, commands, progress, reconnect                   | Independent approval policy or a second execution state machine |
| Coordinator / strategist              | Intent, clarification, workflow proposal, explanations, proposed replanning     | Permission grants or bypasses                                   |
| Technical planner                     | Concrete work items, interfaces, dependencies, test strategy                    | Product decisions silently made on the user's behalf            |
| Deterministic controller              | Contract validation, authority, transitions, dispatch, budgets, stop conditions | Treating model confidence as verification                       |
| Deep Agent workers                    | Bounded investigation, implementation, and review assignments                   | Host access or capabilities beyond their assignment             |
| Workspace and verification services   | Baselines, sandbox operations, candidate integration, checks, artifacts         | Silently modifying the user's checkout                          |
| Durable state / event service         | Authoritative task state, approvals, attempts, replay and recovery records      | Depending on an open Pi terminal                                |
| Publication / deployment integrations | Explicitly authorized GitHub and staging actions                                | Exposing their credentials to repository code                   |

These are responsibility boundaries, not a requirement to create a microservice for each row. Keep the local implementation simple; introduce distributed components in S6 when their failure model is tested.

### Standing invariants

1. The backend owns truth. Pi and GitHub display the same run and contract state.
2. Source files, issue text, tool output, and skill instructions are inputs, not permission grants. Repository conventions cannot expand system capabilities.
3. Approval binds to an exact contract and relevant baseline, policy, model configuration, and environment. An agent's “approved” message is insufficient.
4. Preserve the user's checkout and uncommitted work. Work happens in run-owned isolated copies; a worktree alone is not a security boundary.
5. Provider credentials and publication/deployment credentials remain outside repository execution. A VPC is an additional boundary, not a replacement for a sandbox.
6. Every successful gate identifies the artifact it assessed. Later changes invalidate affected evidence. Deterministic failures cannot be overruled by a reviewer saying “pass.”
7. Verified, user-accepted, applied, published, deployed to staging, and merged are distinct facts.
8. Durable state starts with write-enabled execution. Checkpoint replay must not duplicate side effects; never assume exactly-once delivery.
9. Pause and cancel are acknowledged as complete only after active operations have stopped or settled. Cancellation preserves partial results; it does not imply rollback.
10. Optional skills, plugins, models, and parallelism must demonstrate benefit against a baseline. No automatic package installation or hidden fallback providers.
11. The endorsed model direction is OpenRouter with OpenAI and Anthropic model families excluded. Configuration is explicit; allowed model changes are versioned and evaluated.
12. Production deployment and automatic merging are outside this roadmap. A verified local result does not authorize external publication.

## Shared contracts and lifecycle

### Artifact model

The table specifies information that must remain traceable as the system grows. Some fields are already represented in local schemas; others are requirements for later slices. It is not a claim that every named record already exists as a class or database table.

| Artifact                           | Required information                                                                                                                                                                               | First owning slice                       |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| Request / session                  | Stable ID, origin, repository identity, user instruction, ordered conversation/steering revisions; authenticated actor when remote                                                                 | S1; remote identity in S6                |
| Decision record                    | Question, alternatives, proposed assumption, evidence, blocking scope, answer and who supplied it                                                                                                  | S1                                       |
| Proposal                           | Version, goal, task type, changed/preserved behavior, exclusions, change areas, acceptance criteria, uncertainties, proposed checks and limits                                                     | S1                                       |
| Task contract                      | Canonical version/hash, proposal version, exact source baseline, policy/model configuration, write scope, checks, work items, limits, delivery permission; environment identity as profiles evolve | S2                                       |
| Approval / revocation              | Contract identity, approving principal and channel, timestamp, permitted actions, supersession/revocation; local principal semantics documented                                                    | S2; authenticated remote principal in S6 |
| Run / attempt                      | Contract/approval reference, status/reason, attempt IDs, timestamps, counters, workspace identity, controller ownership; remote lease/fence later                                                  | S3                                       |
| Work item                          | Stable ID, instruction, acceptance responsibility, owned paths, dependencies, baseline/input identity, output and disposition                                                                      | S3; richer DAG scheduling in S5          |
| Check / assurance result           | Check definition, command or review method, environment, artifact identity, exit/outcome, logs, coverage, findings, missing evidence                                                               | S4                                       |
| Deliverable                        | Source revision, resulting content and patch hashes, result revision when applicable, diff summary, evidence manifest, limitations, user acceptance separate                                       | S4                                       |
| Playbook / skill / model selection | Version and provenance, capability requirements, compatible policy, evaluation evidence, selected assignments                                                                                      | S5                                       |
| GitHub / deployment record         | Installation/repository/issue IDs, issue snapshot, delivery IDs, PR/branch, head/base/merge identities, CI runs, deployment artifact/environment and outcomes                                      | S6                                       |

Existing typed local contracts are in [execution_contracts.py](../../tools/shinobi-agent/execution_contracts.py). The plan must evolve them compatibly rather than create a competing schema in Pi.

Keep the decision graph separate from the execution DAG: the first tracks unanswered questions, evidence, and dependencies between decisions; the second schedules approved work items. Resolving a decision can enable a new proposal, but an unresolved product question must never silently become an implementation assignment.

Canonical hashing must be deterministic, schema-versioned, and based on effective semantics. Exclude volatile display timestamps, but include changes that affect authority or evidence. Persist the canonical content alongside its hash. Reject unknown mandatory fields/versions rather than silently dropping constraints.

Every adapter operation needs a request ID and a typed response: success, clarification needed, approval needed, blocked, retryable failure, or terminal failure. A transport timeout means outcome unknown until queried; it must not be interpreted as “nothing happened.” Repeating a request with the same ID and different content is an error. Event cursors support reconnect, ordered rendering, and deduplication; UI progress loss must not lose authoritative events.

### Approval and change rules

| Change                                                                                                                                      | Required response                                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Implementation detail within approved behavior, paths, tools, and budgets                                                                   | Continue; record the decision if material to review                                                                                                     |
| Scheduling change preserving the contract                                                                                                   | Continue within limits; no new authority                                                                                                                |
| New behavior, wider paths, added dependency, new tool/egress access, weakened required check, higher budget, or changed delivery permission | Pause affected execution; issue a new contract and obtain approval                                                                                      |
| Source, policy, environment, or model configuration changes                                                                                 | Revalidate assumptions; reject stale approval where its bound identity changes                                                                          |
| New user direction during unfinished work                                                                                                   | Record it durably before model processing; invalidate conflicting work and approval; preserve unaffected artifacts only with explicit validity evidence |
| User accepts a deliverable                                                                                                                  | Record acceptance; do not infer permission to apply, publish, deploy, or merge                                                                          |

Current local steering conservatively pauses the entire unfinished run and invalidates its proposal. Selective steering remains a future refinement. Repairs retain unrelated completed work while invalidating dependency, input and shared-interface consumers. Approval binds role models, policy, repository HEAD, measured environment, workflow/guidance and protected inputs. See [local commands and approval behavior](../../tools/shinobi-agent/README.md).

### Lifecycle and recovery

These are conceptual stages; map existing status enums to them before any schema migration. Avoid one enormous status enum: execution, publication, CI, staging, and acceptance can have separate revision-bound states.

| Stage / event                          | Controller behavior                                                           | What the user sees                                        |
| -------------------------------------- | ----------------------------------------------------------------------------- | --------------------------------------------------------- |
| Understanding / awaiting clarification | Read permitted evidence; persist decisions; do not dispatch writes            | Question, evidence, proposed assumptions                  |
| Proposed / awaiting approval           | Validate contract; expose exact reviewable contents/hash                      | Scope, checks, limits, exclusions, approval action        |
| Approved / queued                      | Recheck approval and baseline at dispatch; reserve capacity                   | Run ID and queue reason                                   |
| Running / verifying / repairing        | Persist attempts and evidence; enforce bounds and ownership                   | Progress, current phase, remaining allowances             |
| Pause requested → paused               | Stop new dispatch; settle active calls/processes; checkpoint                  | Pending stop until no further writes are possible         |
| Cancel requested → cancelled           | Stop/settle; preserve partial evidence; prohibit further dispatch             | Explicitly incomplete result and recovery options         |
| Interrupted                            | Reconcile actual workspace, processes, budgets, and artifacts before recovery | What survived, what is uncertain, required action         |
| Blocked / needs amendment              | Record reason and affected work; present smallest decision                    | Missing capability, changed scope, or exhausted allowance |
| Failed                                 | Preserve failure evidence; do not publish a successful result                 | Failing gate and actionable explanation                   |
| Locally verified                       | Seal result and evidence; no further edits to that artifact                   | Reviewable patch/branch with limitations                  |
| Published / CI / staging               | Track each gate against the relevant revision/artifact                        | PR, checks, preview, current or stale evidence            |
| Awaiting human merge / merged / closed | Observe authorized human action; retain evidence and clean up by policy       | Final disposition; no autonomous merge                    |

Crash recovery records intent before a side effect and reconciles actual completion afterward. Inspect existing file content, integration pointer, GitHub branch/PR, or deployment identity before retrying. A failed acknowledgement must not duplicate a completed effect. Revoke stale worker authority before recovery dispatch. Corrupt state or missing artifacts blocks recovery instead of reconstructing “success” from chat.

The current local controller survives Pi closure, has explicit recovery, and retains partial artifacts. Its documented limits and recovery behavior are in the [runtime README](../../tools/shinobi-agent/README.md). Distributed leases, failover, and cross-host recovery belong to S6.

## Slice 0: Pi-to-Deep-Agent proof of concept

**Outcome:** demonstrate `user → Pi → extension → Deep Agent → work → visible result` with minimal machinery.

**Entry:** explicitly configured provider/model, supported local runtime, disposable task fixture.

**Current status:** implemented. Preserve the [POC README](../../tools/pi-deepagent-poc/README.md) and [historical evidence](../../tools/pi-deepagent-poc/EVIDENCE.md); do not rebuild it or expand it into a second production runtime.

**Process and deliverables:** the extension forwards a query to the Python runner; the runner instantiates a real Deep Agent with bounded tools; the agent performs a small observable task; the extension displays the actual output or error. Record the query, tool activity, fixture before/after, model, and end-to-end transport evidence. No playbook or skill orchestration is needed here.

**Failures:** unavailable model, malformed bridge output, subprocess failure, and timeout must produce visible failures. Pi-native inference or scripted generation must not masquerade as the live backend.

**Acceptance:** one actual Pi session completes a real-model fixture task; negative controls establish that the backend path was used. Scripted bridge tests remain separate from live evidence.

**Exit:** keep this as the connectivity regression baseline. S1 takes over product behavior; S0 gives no general write authority to later sessions.

## Slice 1: Understand and propose

**Outcome:** the user can say “fix retries,” “investigate this failure,” or “refactor this module,” refine the request, and receive a source-grounded proposal without repository changes.

**Entry:** S0 bridge evidence; source repository readable; durable session store available.

**Current status:** conversation, proposal, revision, resume, read-only boundaries and explicit task classification/changed/preserved behavior are implemented. Local fixtures cover the four task processes. Clarification quality and broader decisions remain model-dependent; arbitrary repository competence is not established.

### Work and interaction

- **S1.1 — Intake:** capture goal, task type, changed/preserved behavior, constraints, exclusions, repository/baseline, and examples of success. Confirm an ambiguous type only when it changes behavior or verification.
- **S1.2 — Discovery:** inspect relevant source, callers, repository instructions, and available check definitions. Record evidence paths and the inspected baseline. Do not run repository code merely because the user requested an explanation.
- **S1.3 — Decisions:** distinguish blocking product questions from routine implementation choices. Keep assumptions explicit. An investigation can finish with supported uncertainty; a write contract cannot hide unresolved decisions that materially change scope.
- **S1.4 — Proposal:** present behavior, likely change areas, acceptance examples, standing quality gates, proposed checks/environment, risk, limits, and delivery mode. If diagnosis needs execution, propose a separately bounded diagnostic contract through S2–S4.
- **S1.5 — Conversation:** persist follow-up instructions and proposal versions; resume the same session after restart. Explain what changed between proposals. State errors without losing user input.

**Example:** “Cap reconnect delay at ten seconds; keep the public function signature unchanged” becomes acceptance for the cap, existing edge cases, API preservation, permitted files, and checks. “Looks good” in ordinary chat does not bypass the explicit execution approval flow.

**Outputs and ownership:** request/session, evidence references, decision records, versioned proposal. The coordinator drafts; the backend stores and validates; Pi renders and collects answers.

### Failures and acceptance

| Test                                                                      | Required observation                                                           |
| ------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| S1-T1: vague request and materially different interpretations             | Targeted clarification; no invented product decision                           |
| S1-T2: grounded question with sufficient evidence                         | Useful proposal with references and executable verification direction          |
| S1-T3: restart, resume, then refine a constraint                          | Latest direction retained; old proposal visibly superseded                     |
| S1-T4: source/tool text says to write, reveal secrets, or ignore approval | No capability escalation or unauthorized write                                 |
| S1-T5: model error, malformed response, or context growth                 | Input retained; typed failure or evidence-backed summary; no fabricated result |
| S1-T6: binary, oversized, symlink, missing, or unsupported source         | Explicit discovery limitation; no claim that excluded content was inspected    |

**Exit gate:** the real Pi path produces a useful, resumable proposal and source remains unchanged. Supported discovery limits are visible. Open material questions block S2 approval.

**Out of scope:** executable diagnosis, implementation, automatic publication, and skill orchestration.

## Slice 2: Approve a task

**Outcome:** the user reviews one concrete contract and authorizes bounded execution, including routine repairs, without approving every edit.

**Entry:** S1 proposal with resolved blocking decisions; explicit repository baseline and viable verification plan. Execution can remain disabled until S3 and S4 are ready.

**Current status:** schema-2 contracts bind exact hash approval to effective environment, workflow, role models, reviewed guidance and protected inputs; Pi displays the full effective authority. Drift is rechecked and legacy raw records remain inspectable but cannot execute under the new policy. See [contract schema](../../tools/shinobi-agent/execution_contracts.py) and [approval UX](../../tools/shinobi-agent/README.md). Remote actor identities, visual contract diffs and approval expiry remain future work.

### Work and interaction

- **S2.1 — Compile:** turn the proposal into a typed contract containing scope, behavior, acceptance, explicit paths, checks, dependency graph, tool/environment permissions, budgets, exclusions, and delivery mode. Reject empty acceptance, missing checks, unresolved scope, duplicate IDs, cycles, invalid dependencies, and unowned writes.
- **S2.2 — Review:** show the full effective contract and a concise summary, including what may change and which checks are mandatory. Hash approval must refer to exactly those contents, not a different hidden configuration.
- **S2.3 — Authorize:** use an explicit backend-validated action. Current local flow is `/shinobi-contract`, then `/shinobi-approve <hash>`. Persist approval before queueing. Repeat approval must return the same run or disposition, not launch another attempt unintentionally.
- **S2.4 — Recheck:** validate baseline, policy, permissions, and contract identity at dispatch and recovery. Serialize approval versus steering/revocation so stale work cannot start through a race.
- **S2.5 — Amend:** show a contract diff when scope or privileges change. Preserve prior evidence as historical, invalidate obsolete approval, and require approval of the new version. Replanning must not reset repair/cost limits silently.

**Local identity:** document the trust assumption that the authorized local operator controls the backend state and approval channel. Do not claim this authenticates arbitrary remote users. S6 introduces verified GitHub identities and per-repository authorization.

**Budget baseline:** current local defaults are one worker, two repair cycles, one replan, 900 seconds wall time, 60 model calls, and 30 graph steps. The schema caps workers at two, repairs at two, and replans at one. Current wall time includes pauses. These are existing defaults, not an established optimal policy. There is no current hard dollar cap; adding one requires reliable accounting and enforcement rather than displaying an estimate as a guarantee. See [limits](../../tools/shinobi-agent/execution_contracts.py).

### Failures and acceptance

| Test                                                                   | Required observation                                                 |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------- |
| S2-T1: exact approval; repeated same approval                          | One authorized run; stable audit reference                           |
| S2-T2: stale hash, changed source/policy/model, or unresolved decision | Rejection with reason; no write dispatch                             |
| S2-T3: concurrent approval and steering/revocation                     | A single valid ordering; obsolete authority cannot dispatch work     |
| S2-T4: cycle, invalid path, missing check, or unowned write scope      | Invalid contract rejected before execution                           |
| S2-T5: unapproved dependency, check weakening, or budget increase      | New reviewable contract required                                     |
| S2-T6: approval response lost, client retry, or unknown schema         | Query/deduplication or explicit incompatibility; no silent duplicate |

**Exit gate:** every executable run has a valid durable approval for its exact contract; malformed/stale contracts cannot execute. Authority and UI display agree. No implementation is needed to prove rejection paths.

**Out of scope:** GitHub permission resolution and cloud privileges; they extend the same contract in S6.

## Slice 3: Implement one task

**Outcome:** one approved work item runs independently of Pi in an isolated workspace and produces an inspectable candidate without touching the user's checkout.

**Entry:** S2 valid approval; sandbox preflight; supported execution profile; S4 verifier available before exposing a successful end-to-end task flow.

**Current status:** detached execution, isolated copies, scoped writes, durable attempts, controls and recovery exist. The measured offline Linux profile binds installed executable hashes/versions, backend/controller identity, kernel/architecture, committed dependency metadata and permissions. Diagnostics expose no source mutation tools; missing dependencies block before implementation. This is not a hermetic system-library image or aggregate cgroup quota. Arbitrary dependency environments remain unsupported. See [sandbox and environment limits](../../tools/shinobi-agent/README.md).

### Work and interaction

- **S3.1 — Baseline:** capture exact committed source and file metadata. Show excluded dirty/untracked changes. Current runs preserve those user changes but do not incorporate them. If they matter to the task, block or obtain an explicit future snapshot policy; never silently discard or pretend to include them.
- **S3.2 — Preflight:** verify sandbox availability, capabilities, source limits, tools, and check prerequisites before a costly run. Current symlink/submodule exclusions and snapshot limits must produce clear errors. Preserve binary content and executable modes where supported.
- **S3.3 — Environment:** use a versioned execution profile identifying runtime/tool versions, dependencies/lockfile, architecture, allowed commands, network, writable mounts, and resource limits. The existing offline profile is the initial baseline. A dependency bootstrap is separate, explicitly authorized work with isolated credentials/network and immutable output; never silently install on the host.
- **S3.4 — Execute:** assign one implementer the approved instruction, relevant evidence, explicit tool capabilities, owned paths, and limits. Validate writes in a deterministic service. Agent-side advisory checks do not replace S4 checks. Repository commands may have side effects even when their name sounds like a test; contain them in the sandbox.
- **S3.5 — Persist:** record attempt start, tool intents/results, workspace and candidate identity, budgets, and outcome. Model/tool timeouts, output truncation, and context limits are explicit. A transport disconnect cannot manufacture task completion.
- **S3.6 — Control:** expose status, pause, continue, cancel, steer, and recovery. Stop new dispatch first, settle active operations, then acknowledge the stopped state. Current commands are documented in the [runtime command table](../../tools/shinobi-agent/README.md).
- **S3.7 — Package candidate:** generate an immutable candidate and diff with provenance. Route it to S4. A no-op is valid only if the request was already satisfied and evidence supports that outcome; otherwise it is incomplete.

**Credential boundary:** model coordination occurs outside repository execution. Tools receive the minimum capability they need. Block host home/state paths, traversal, escape through symlinks, network outside policy, and implicit default agent tools/delegation. Repo-controlled hooks and filters cannot run in trusted host inspection.

**Current resource limitation:** per-process limits and namespace isolation are not aggregate cgroup memory/PID quotas. Treat this as a documented local limitation; S6 requires production aggregate quotas and isolation appropriate to remote untrusted jobs.

### Failures and acceptance

| Test                                                                              | Required observation                                                                         |
| --------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| S3-T1: one small real task                                                        | Candidate changes only approved areas; user checkout and pre-existing edits remain unchanged |
| S3-T2: unauthorized path, host read, credential read, network, hook/filter escape | Denied or contained; no secret leakage or host side effect                                   |
| S3-T3: sandbox/dependency/tool unavailable                                        | Blocked with capability explanation; no host fallback                                        |
| S3-T4: Pi closes while run is active                                              | Controller continues; resumed Pi shows authoritative state                                   |
| S3-T5: pause/cancel during tool or model activity                                 | Pending status until settled; no writes after final acknowledgement                          |
| S3-T6: controller crash before/after a write or integration boundary              | Recovery reconciles actual content; no duplicate edits or false success                      |
| S3-T7: source drift, quota exhaustion, disk full, malformed model output          | Bounded failure or amendment; retained partial artifacts and honest reason                   |
| S3-T8: binary/executable file and ignored tracked content                         | Supported bytes/modes retained; unsupported content is explicitly rejected                   |

**Exit gate:** an approved task produces a candidate through the real Pi/backend path; isolation, lifecycle, and recovery tests pass for the supported profile. Delivery as “verified” waits for S4.

**Out of scope:** unrestricted dependency installation, broad host shells, remote workers, or automatic application to the source checkout.

## Slice 4: Verify and repair

**Outcome:** the system determines whether the candidate satisfies the contract, repairs supported failures within bounds, and returns evidence that the user can inspect.

**Entry:** S3 immutable candidate, explicit checks/environment, acceptance criteria, and remaining repair allowance.

**Current status:** independent baseline/combined checks, fresh read-only assurance, bounded repairs and patch delivery exist. Existing selected test/config inputs are hash/mode protected; edits require an oracle amendment. Empty, skipped or reduced unittest suites cannot pass. Infrastructure/evidence/provider failures do not consume code repairs. A no-op needs passing baseline checks and explicit independent already-satisfied evidence. Broader environments, flaky-test exceptions and realistic repository quality remain open. See [verification and artifacts](../../tools/shinobi-agent/README.md).

### Work and interaction

- **S4.1 — Establish baseline:** record which approved checks fail before changes when diagnosis requires it. For a bug, retain the original reproduction and expected corrected behavior. Distinguish pre-existing failures, introduced failures, and unavailable checks. A task cannot pass by silently waiving a mandatory failure.
- **S4.2 — Verify externally to the implementer:** the controller executes mandatory checks on the sealed combined candidate in the declared environment. Store command, inputs, exit code, duration, relevant logs, environment identity, and content identity. Worker claims or pasted logs are insufficient.
- **S4.3 — Protect the oracle:** bind check definitions and expected assertions to the approval or independently maintained fixtures. Inspect test/config changes for deleted assertions, skipped tests, reduced scope, and altered runner behavior. Changing tests can be legitimate but must not let the worker redefine success. New legitimate expectations require justified review; weakening a required gate requires amendment.
- **S4.4 — Independent assurance:** use a fresh reviewer context with the contract, baseline/candidate diff, check evidence, and relevant source. Require coverage for every acceptance criterion, concrete findings, affected work, and pass/change-required/amendment disposition. Independence means separate review execution and read-only capabilities; a different model is an optional evaluated policy, not automatic proof.
- **S4.5 — Repair:** attribute actionable failures to work items; preserve unaffected valid outputs; repair within approved paths and total allowance. Re-run affected checks and mandatory combined verification. Do not bypass a gate because it is inconvenient or flaky. Unresolved product decisions or expanded scope return to S2.
- **S4.6 — Seal and deliver:** bind diff, content hash, patch hash, checks, assurance, environment, and known limitations in an evidence manifest. Show the user what changed, why, what ran, what did not, and how to inspect the local patch/run-owned branch. Applying it remains a separate authorized operation.

**Failure taxonomy:** distinguish code/test failure, environment failure, provider failure, policy denial, evidence failure, and exhausted budget. Infrastructure retries must be bounded and separately recorded. Current production model configuration has no implicit retry/fallback; any added retry policy must count attempts and ambiguous outcomes explicitly. Do not spend repair allowance on infrastructure recovery without a defined rule, and do not give code repairs unlimited retries by calling them infrastructure failures.

**Flaky and missing checks:** a timeout or skipped check is not a pass. A rerun retains all prior outcomes. A known flaky test can have an explicit approved policy, but must not be silently excluded. If required evidence cannot be obtained, deliver a blocked/incomplete result with the partial patch, not “verified.”

### Failures and acceptance

| Test                                                                                | Required observation                                               |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------------ |
| S4-T1: correct fix with original reproduction and regressions                       | All required checks and acceptance coverage pass for exact result  |
| S4-T2: plausible patch that fails a deterministic check                             | Reviewer cannot override failure; bounded repair or failure        |
| S4-T3: deleted assertion, skipped test, edited check configuration                  | Weakening detected; no false success                               |
| S4-T4: missing criterion or evidence from another revision                          | Assurance fails closed; stale result not delivered as verified     |
| S4-T5: repair fixes one behavior but breaks another                                 | Combined checks run again and catch the regression                 |
| S4-T6: exhausted repairs, flaky check, environment failure, reviewer/provider error | Truthful distinct outcome; no hidden retry loop                    |
| S4-T7: sealed artifact edited afterward                                             | Hash mismatch invalidates evidence and blocks verified delivery    |
| S4-T8: no-op or partially completed request                                         | Explicit supported already-satisfied outcome, or incomplete result |

**Exit gate:** at least one realistic approved task completes end to end, and deliberately incorrect candidates are rejected. The manifest can explain every required criterion and is tied to exact bytes. Small fixture success alone does not establish broad repository quality.

**First useful local release:** S1–S4 together. Verification is mandatory for this release, even if S3 and S4 are developed separately. No specialist ecosystem or cloud deployment is required.

## Slice 5: Add specialist workflows

**Outcome:** the coordinator chooses an appropriate process and bounded specialists, coordinating larger work only when it improves results.

**Entry:** stable S1–S4 controls and baseline evaluation; replayable contracts/evidence; a supported task corpus. Parallelism must not be used to compensate for missing single-worker correctness.

**Current status:** four versioned playbooks, three original MIT guidance entries, explicit role-model selection, at most two workers, declared input/interface-aware scheduling and transitive repair invalidation are implemented. Attempts bind consumed input manifests. A versioned six-case corpus compares sequential/two-worker configurations with independent judges and predeclared review thresholds. [Current evidence](../../tools/shinobi-agent/LOCAL_S5_EVIDENCE.md) separates scripted repetitions from live acceptance. No default parallel routing change is justified. External skills/Pi packages, selective steering, broad repository quality and repeated live cost/throughput comparisons remain future work.

### S5A — Task-specific playbooks

| Task type     | Process                                                                                                                                                                    | Mandatory completion evidence                                                                                        |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Investigation | Clarify question → read evidence → compare explanations → permitted diagnostic experiment if separately approved → synthesize                                              | References, observations, competing explanations, limits, actionable conclusion; no forced code change               |
| Bug fix       | Capture symptom → approved reproduction → causal explanation → approve fix contract → implement → repeat original reproduction → regressions → assurance                   | Original symptom addressed on the same relevant surface, no required regression failures                             |
| Feature       | Clarify changed behavior → design interfaces and examples → approve → implement bounded increments → integrate → verify acceptance → assurance                             | New behavior, edge/error paths, compatibility and integration evidence                                               |
| Refactor      | Define preserved behavior/API/performance constraints → characterize existing behavior → approve structural change → refactor incrementally → compare behavior → assurance | Identified behavior preserved, structural objective achieved, required performance or compatibility checks satisfied |

Executable diagnosis needs its own approved diagnostic capability before a fix proposal can depend on it. A diagnostic contract is read-only with respect to source writes, but may permit sandbox-local process side effects. Its findings feed a new implementation proposal; it does not authorize the fix automatically.

Define playbook input/output contracts, mandatory gates, eligible tools, stop conditions, and escalation paths. Do not force every task through every specialist. Investigations may finish at S1; high-risk migrations, destructive data changes, security-sensitive deployment, or unknown repository stacks require a dedicated approved playbook or a supported blocker.

### S5B — Roles, skills, and Pi packages

- Explorer gathers evidence; planner designs changes; implementer changes assigned files; reviewer challenges results. The strategist selects the process. Every delegated call receives explicit model, tools, policy, input identity, budgets, and expected output.
- A role is responsibility, a skill is guidance, a playbook is process, and policy is authority. Keep these distinct in configuration and logs.
- Curate versioned guidance inspired by Matt Pocock's questioning/decomposition, Addy Osmani's Definition of Done and constraint-driven checks, and pstack's reproduction/impact/verification practices. Preserve license/provenance and review each adaptation; historical inspiration is not a verified compatible package integration.
- Reject guidance that bypasses approval, auto-publishes, introduces disallowed provider defaults, writes outside scope, or assumes tools are present. Test prompt-injection attempts through both repository content and imported guidance.
- Pi package candidates such as plan review, clarification, todo display, and tracing remain optional. Pin and evaluate compatibility and permissions; backend state remains authoritative. A Pi-native tool or subagent plugin does not automatically become a Python Deep Agent capability.
- Define context handoffs: relevant source/evidence references and decisions, not unrestricted transcript dumping. Summaries retain constraints and provenance. Missing context triggers a read or clarification rather than an invented assumption.

### S5C — Dependency graph and integration

1. Build a validated DAG of bounded work items with acceptance responsibility, file ownership, shared interfaces, dependencies, and outputs.
2. Dispatch ready independent work under run/repository/global limits. Disjoint paths are insufficient if workers share incompatible assumptions or modify producer/consumer contracts.
3. Give each worker an isolated baseline. When prerequisite output changes, refresh or invalidate downstream work; never silently apply it to the wrong candidate.
4. Integrate candidates sequentially with a transactional current-candidate pointer. Record accepted/rejected outputs and preserve provenance.
5. Treat integration conflicts as explicit repair or replanning work; no silent “last writer wins.” Re-run combined verification after integration.
6. On steering or a failed prerequisite, invalidate affected items and transitive dependents. Retain unrelated results only when their inputs and assumptions still hold. Keep current whole-run pause as the fallback until selective steering is proven.
7. Enforce total budgets across all workers and repairs. Worker restarts, replans, or splitting tasks must not reset the overall allowance.

### S5D — Model and workflow improvement

Keep a single-worker baseline. Evaluate role/model assignments, skill versions, playbooks, and worker counts on the same versioned tasks, with repeated runs for stochastic behavior. Measure accepted-correct completion, false-success rate, unauthorized actions, human interventions, total cost per successful task including failed attempts, wall time, and repair counts. Track raw token/call usage; unknown provider cost remains unknown, never zero.

Define model capability checks for tool calling, structured outputs, long-context handling, cancellation/error behavior, and quality on relevant tasks. Version every configuration used in comparisons. Change the approved routing configuration through policy/contract versioning; do not substitute a fallback model mid-run without authority.

### Failures and acceptance

| Test                                                                             | Required observation                                                                  |
| -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| S5-T1: investigation, bug fix, feature, and refactor cases                       | Correct process and required evidence; no unnecessary write flow                      |
| S5-T2: malicious/incompatible skill or plugin; delegation missing a policy       | Rejected or constrained; no authority escalation                                      |
| S5-T3: independent tasks, overlapping files, and disjoint but coupled interfaces | Safe scheduling; semantic conflicts caught before verified delivery                   |
| S5-T4: upstream repair, integration conflict, or mid-run steering                | Correct dependent invalidation; valid unrelated outputs retained with evidence        |
| S5-T5: worker crash or exhausted shared allowance                                | Bounded recovery; no orphan worker or multiplied budget                               |
| S5-T6: baseline versus specialist/parallel configuration                         | Reproducible comparison; no adoption based solely on agent claims or one fast fixture |

**Exit gate:** the four supported task processes have real examples and negative tests; specialist additions meet predeclared quality/cost criteria; combined verification remains mandatory. Parallelism may remain disabled by default if benefit is not demonstrated.

**Out of scope:** an open plugin marketplace inside trusted workers, unlimited delegation, automatic skill installation, or a claim that every repository/task type is supported.

## Slice 6: Run through GitHub and VPC workers

**Outcome:** an authorized user selects an issue, authorizes bounded work, receives a verified PR with current CI/staging evidence, and decides whether to merge.

**Entry:** S1–S4 correctness and recovery gates; S5 components only where required by the chosen remote workflow. The first remote release may use one implementer and no skills. Resolve decisions D6–D12 below before dependent provisioning or external writes.

**Current status:** planned. The local controller, IDs, contracts, and artifacts are reusable foundations, but local SQLite/locks and synthetic result commits do not by themselves constitute a distributed production service.

### S6A — GitHub intake, identity, and approval

**Work:** select an explicit trigger, such as a GitHub App command or manually dispatched workflow. Verify installation/repository identity and the actor's current permission for trigger, approval, amendment, cancellation, and retry. Capture issue ID, title/body snapshot, relevant attachments as untrusted input, request ID, and source revision. A label or issue edit alone is not unlimited implementation permission.

Receive events through authenticated HTTPS webhook handling, validate signatures, allowlist event/action types, enqueue durable work, and deduplicate delivery IDs. Reject invalid signatures and unsupported installations before agent dispatch. GitHub recommends webhook secrets and event validation; delivery and queue handling must follow its [webhook guidance](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks), checked 2026-10-10.

**User flow:** user selects issue → backend investigates → GitHub displays proposal and contract identity → authorized user approves that version → run queues. A future preapproved issue template is possible only if it represents the same complete bounded contract and verified authority. Issue edits during a run become proposed steering; they cannot silently mutate the approved contract.

**Artifacts:** authenticated request, issue snapshot, approval, stable issue/run correlation, deduplicated event record. Minimize GitHub comments by updating a stable status surface; publication of comments is an explicitly configured integration permission.

**Gate:** valid trigger/approval works; forged, repeated, unauthorized, edited, and out-of-order events cannot start obsolete or duplicate work. Permission revocation prevents new privileged actions and follows a documented active-run policy.

### S6B — Durable control plane and queue

**Work:** separate adapter requests, durable orchestration, queue dispatch, worker execution, artifact storage, and publication. Choose transactional shared state and object storage; retain local development support behind the same logical interfaces. Version the API and schema; back up state before migrations and test upgrade/recovery on interrupted runs.

Use durable queued jobs, idempotency keys, worker leases/heartbeats, and fencing tokens. Queue redelivery cannot authorize two active owners to integrate or publish one attempt. If the controller cannot confirm authority, it must stop further privileged actions. Reconcile lost leases and ambiguous side effects before replacement dispatch.

Bound concurrency per tenant, repository, run, and globally; apply queue fairness and backpressure. Preserve a conservative one-active-writer-per-repository default until safe concurrent-run policy is proven. Distinguish queue time from active runtime, and define whether pause consumes each allowance. Remote budget semantics must be explicit rather than silently inheriting unsuitable local timers.

**Artifacts:** durable job/attempt, lease/fence, budget reservation, event/outbox records, content-addressed artifacts, retention metadata. Database/file references must be portable across hosts; `/tmp` paths are insufficient remote evidence.

**Gate:** duplicate queue deliveries, worker loss, controller restart, storage timeout/full conditions, and network partitions cannot create concurrent unauthorized writers or false success. Restore state and artifacts from backup in a tested exercise before production use.

### S6C — VPC worker and execution environment

**Work:** choose provider and worker hosting after D8; build a disposable worker with the same bounded assignment contract as local execution. Use pinned images, immutable dependency profiles, explicit egress, isolated workspaces, aggregate CPU/memory/PID/disk limits, and execution deadlines. Keep model access mediated outside repository code and publication credentials in a separate service.

Define checkout credentials, approved dependency registries, package integrity/lockfile handling, and lifecycle-script policy. Isolate bootstrap from execution where privileges differ. Do not cache writable artifacts across tenants or trust a previous job's cache without provenance validation. Block cloud metadata/management endpoints from untrusted execution.

Provision only with explicit infrastructure approval. Preflight capacity, region/network, required tools, and budget before dispatch; unsupported environments return a typed blocker. Encrypt sensitive stored state, redact logs, and authorize access to source/artifacts by tenant/repository. Test actual isolation; a private subnet alone is insufficient.

**Gate:** real remote task completes in the selected VPC with evidence; cross-run/tenant access, secret/metadata access, unauthorized egress, resource exhaustion, cancellation, and stale-worker actions are denied or contained. Worker cleanup happens only after durable artifact export or explicit retention of an incomplete result.

### S6D — Verified result to pull request

**Work:** publication is a separately authorized capability. Recheck approval, result hashes, repository destination, branch policy, and current base. Construct a real Git commit with valid target-repository ancestry from verified changes. The current local result can be a synthetic commit; do not push it assuming it has the intended GitHub ancestry. Compare the reconstructed tree to verified content and rerun gates whenever inputs/content change.

Use a stable branch/run mapping and duplicate-safe create/update logic. Reconcile existing remote branch and PR after timeouts. Never overwrite unexpected human commits or force-push user branches. Detect base drift and follow an explicit rebase/amendment policy; changes invalidating approved assumptions require renewed approval. Reverification is required for altered candidates.

Create a PR linked to the issue with behavior summary, scope, checks, artifact identities, and limitations. The publication identity must have only required repository permissions; workers cannot obtain its token. Repeated events must not produce duplicate PRs/comments or close the issue prematurely.

**Workflow trigger detail:** bot-created PRs must actually start the intended checks. GitHub's current behavior includes approval-required runs for certain `pull_request` events created using `GITHUB_TOKEN`; other event propagation remains restricted. A GitHub App installation token is the proposed approach when automatic PR workflow triggering is required. Verify the chosen token/event combination in the actual repository rather than assuming either universal suppression or universal execution. See [GitHub workflow trigger rules](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow), checked 2026-10-10.

**Gate:** one verified result creates exactly one appropriate PR, records its actual head/base, and starts expected CI. Ambiguous publication, expired credentials, source drift, and human branch edits fail safely with reconcilable state.

### S6E — GitHub CI and staging before merge

**Work:** require GitHub CI independently of worker checks. Identify whether each check assessed the PR head, a merge candidate, or a build artifact; record all relevant identities. Verify check origin, required check set, conclusion, and freshness. Missing, skipped, cancelled, stale, or spoofed status is not a required pass.

Do not execute untrusted PR code in a privileged `pull_request_target` job. If the repository uses a merge queue, required workflows must handle `merge_group`. These are distinct event/security concerns in [GitHub's workflow event reference](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows), checked 2026-10-10.

Build a traceable immutable deployable artifact from the candidate that passed required checks. Choose per-PR preview or serialized shared staging; define isolated test data, secrets, reversible migrations, smoke/acceptance checks, URL access, teardown, and deployment rollback. Staging must validate the candidate **before** human merge. Production data and production deployment are excluded.

Use environment protections compatible with the repository's GitHub plan/visibility; availability varies. A staging approval, if required by deployment policy, is a separate explicit gate and is not equivalent to merge approval. See [GitHub environment rules](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments), checked 2026-10-10.

On a new PR commit, mark older CI/staging evidence stale, stop or supersede older deployments, and validate the current candidate. A late event for an old commit cannot make the current PR green. Shared staging needs a lease so one PR cannot be verified against another PR's deployed content.

**CI repair policy:** proposed default is report-and-pause initially. If automatic repair is later enabled, it requires the same contract, remaining total repair allowance, fresh local verification, updated PR, and fresh CI/staging. It cannot reset the budget or approve expanded scope. Environment outages must be distinguishable from code failures.

**Gate:** a real bot-created PR passes intended CI, deploys the correct artifact, passes staging checks, and displays current evidence. Test failed checks, malicious PR contents, new commits mid-deploy, shared staging collisions, failed migration/deploy, and failed cleanup. No gate silently counts a stale artifact as current.

### S6F — Human merge and operations

**Work:** provide one status view linking issue, contract, run, PR, current CI, staging artifact/URL, and unresolved findings. Once gates pass, the system is awaiting human merge. Configure branch protections and app permissions so the agent cannot bypass required checks or merge on its own. A human may reject or close the PR; record that outcome without treating it as agent failure or permission to retry indefinitely.

Observe merge/close and execute the authorized retention/cleanup policy: stop outstanding work, tear down preview environments, release leases, expire credentials, retain required audit/evidence, and delete disposable workspaces safely. Cleanup failures are visible and retried within an operations budget. Closing an issue during execution must have a defined stop policy.

Establish service health metrics, alerts, operating runbooks, backup/restore, credential rotation/revocation, incident shutdown, rollout/canary controls, and schema/worker-version compatibility. An operator kill switch stops new dispatch and publication without destroying evidence. Define ownership for stuck jobs, orphan workers, unexpected cloud spend, and staging leaks.

**Gate:** a selected issue completes through real VPC execution, PR, CI, staging, and manual merge in a controlled test repository. A second exercise covers interruption/recovery and a third covers rejection/closure/cleanup. Evidence proves the agent had no automatic merge or production deployment path.

**S6 exit:** S6A–S6F all pass. Provisioning a worker or opening a PR alone is not completion of the software factory.

## Testing and continuous improvement

### Test layers

| Layer                                 | Purpose                                                                   | Expected use                                                      |
| ------------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Deterministic contract/state tests    | Approval validity, transitions, scope, budgets, replay, graph ownership   | Every relevant change; no paid model required                     |
| Adapter/protocol tests                | Actual Pi extension and subprocess behavior; later signed GitHub fixtures | Every protocol change; fake generation identified explicitly      |
| Sandbox/environment tests             | Filesystem, network, credentials, process lifecycle, check tooling        | Every sandbox/profile change on supported hosts                   |
| Scripted end-to-end tests             | Full controller/workspace/check/reviewer flow with controlled generation  | Repeatable correctness and injected-failure coverage              |
| Live local acceptance                 | Real Pi, configured real model, actual tools and evidence                 | Each material runtime/model change; record cost and artifacts     |
| Real-task evaluation                  | Coding quality, false success, human effort, cost and time                | Before adopting playbooks, skills, routing, or higher parallelism |
| Remote acceptance / failure exercises | Actual GitHub token/events, VPC worker, CI, staging, merge observation    | Before S6 release and relevant infrastructure upgrades            |

Do not substitute unit tests for full-path evidence, or live success for deterministic negative tests. Credential/sandbox restrictions produce blocked or skipped outcomes, never an invented pass. Test success cannot itself authorize new implementation or privileges.

The supported task corpus should include an investigation with uncertainty, a reproducible bug, a feature, a behavior-preserving refactor, a missing-dependency task, stale approval, malicious repository instructions, a weakened test, a crash after a side effect, coupled parallel changes, and stale CI/staging events. Include deliberately impossible/out-of-scope requests that must stop correctly.

Use versioned fixtures and a held-out set. Predeclare success criteria and practical improvement thresholds before comparing candidates. Repeat stochastic runs and report sample counts and variability; do not invent confidence from a single pass. Separate a correct blocked outcome from task completion. Human acceptance can reveal missed requirements even after technical verification.

### Observability and evidence quality

Use correlation IDs across session, request, contract, run, attempt, worker, check, issue, PR, and deployment. Record structured events for approval, denial, state changes, budget consumption, check outcomes, repairs, interruption, recovery, and external effects. UI summaries must be derivable from those records.

Track queue/active/paused time separately, model/tool calls, token usage when available, estimated versus billed cost, failure category, repair count, and human interventions. Redact secrets and sensitive source from routine telemetry. Raw prompts and model traces require a deliberate retention/access policy; external tracing is not enabled implicitly. Logs are useful evidence but not an authority source.

Every release report records source SHA, dependency/model/policy/playbook versions, environment, commands, which generation was scripted/live, result artifacts, known failures, and unresolved limitations. Export evidence from ephemeral locations before deleting them. Hashes detect changed content but do not by themselves prove that checks were trustworthy; trusted controller provenance and protected check inputs matter.

### Definition of done for a development increment

- Approved scope and expected behavior are explicit; unresolved material choices are resolved or excluded.
- Normal, negative, interrupted, and recovery behavior is implemented for the touched boundaries.
- Relevant deterministic checks pass; full-path/live evidence is added when the changed behavior needs it.
- Existing security/approval boundaries remain enforced, including under malicious inputs.
- Protocol/schema/config changes have compatibility and migration behavior; rollback does not reinterpret old approval as new authority.
- Documentation, operator/user errors, evidence, supported limits, and this roadmap's status are updated together.
- No unsupported claim of broad quality, production readiness, cost improvement, or completion is made from a narrow fixture.

For runtime changes, use the applicable Nx targets documented in the [runtime README](../../tools/shinobi-agent/README.md). The approved increment requires regression, negative-boundary, Pi integration and workflow evaluation evidence. Formatting/link review is sufficient only for later documentation-only edits.

## Decisions and release gates

These decisions are deliberately not silently resolved by the plan. An implementation handoff can choose a narrower supported scope, but must document that boundary and its blocker behavior. “Owner” identifies the decision role; implementation starts only after the relevant logic is approved.

| ID  | Decision and proposed starting point                                                                                      | Owner                                             | Must close before                                           | Evidence of closure                                                           |
| --- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- | ----------------------------------------------------------- | ----------------------------------------------------------------------------- |
| D1  | Supported repository profiles: keep current offline Python/system-tools baseline; add other stacks one profile at a time  | User + runtime maintainer                         | Advertising another stack in S3/S4                          | Approved profile, representative task, missing-dependency and isolation tests |
| D2  | Dirty/untracked source: current committed-baseline-only behavior; defer inclusion until explicit snapshot semantics exist | User + workspace maintainer                       | Tasks requiring local unpublished content                   | Reviewed inclusion/exclusion policy and exact-byte/preservation tests         |
| D3  | Stronger local resource limits, environment fingerprint, and dependency bootstrap policy                                  | Runtime/security maintainer + user for privileges | Expanding local environment; mandatory remote quotas in S6C | Threat-boundary tests and versioned profile contract                          |
| D4  | Verification oracle ownership, standing DoD, flaky-test policy, allowed test changes                                      | Repository owner + assurance maintainer           | Broad S4 release                                            | Protected checks and seeded false-success rejection                           |
| D5  | Playbook/skill/package selection, permitted models and routing, evaluation thresholds                                     | User + workflow maintainer                        | Enabling each S5 addition                                   | Pinned provenance, compatibility review, baseline comparison                  |
| D6  | GitHub trigger and approval UX; exact identity-to-permission rules                                                        | User/repository administrator                     | S6A integration                                             | Accepted sequence and unauthorized/revoked-actor tests                        |
| D7  | Issue editing/closing, approval expiry/revocation, base drift, human branch changes                                       | User + controller maintainer                      | S6A/S6D write path                                          | Explicit transition rules and race/recovery tests                             |
| D8  | Cloud/VPC provider, region, worker hosting, network/dependency policy                                                     | User + infrastructure owner                       | S6C provisioning                                            | Approved architecture, cost estimate, isolated pilot; no provider assumed     |
| D9  | Shared database/queue/artifact store, leases, retention, backup and migration strategy                                    | Controller/infrastructure maintainer              | S6B release                                                 | Redelivery/failover, restore, tenant isolation, cleanup tests                 |
| D10 | GitHub App permissions, branch naming, publication authorization, CI event configuration                                  | Repository administrator                          | S6D publication                                             | Actual bot PR triggers correct CI with minimum permissions                    |
| D11 | CI auto-repair: initially report-and-pause; staging topology/protections/test data/migrations                             | User + repository/deployment owner                | S6E deployment                                              | Chosen flow, stale-event/collision/rollback tests, budget behavior            |
| D12 | Concurrency/fairness, hard spend controls, stop behavior, service objectives, retention and incident ownership            | User + operations owner                           | S6 production use                                           | Load/failure exercise, alerts, kill switch, documented runbooks               |

A decision's absence is a release blocker for the dependent capability, not a reason to block unrelated local work. Local S1–S5 approval does not grant permission to create cloud resources, send GitHub messages, publish, or deploy.

Local decisions implemented under the approval:

- **D1/D2:** offline Linux system tools and committed-only source; other stacks and unpublished-source inclusion remain unsupported.
- **D3:** schema-2 measured profile and fail-closed environment drift. Dependency bootstrap, hermetic images and aggregate cgroup quotas remain deferred.
- **D4:** freeze selected existing oracle files and inline argv, observe the unchanged baseline, require refactor characterization, reject skipped/missing evidence, and allow new tests only inside approved ownership. Changing the selected oracle needs a new contract; no flaky-test exception is implicit.
- **D5:** four repository-owned playbooks, three original MIT guidance entries, explicit compatible role models, default one worker, and a six-case corpus. Adoption review requires three repetitions per case/configuration, held-out coverage, no false/unauthorized success, quality at least baseline and 10% measured latency or known-cost gain. Scripted generation cannot qualify and adoption is never automatic. Broader task quality, repeated live comparisons, external guidance/Pi packages and measured human effort/provider costs remain open.

D6–D12 remain unresolved for S6. No cloud provider, repository identity, shared storage, GitHub App, staging topology, retention or hard-spending policy has been inferred.

## Coverage and execution order

### Requirement traceability

| Required capability                                                                 | Owning slice / section             | Completion evidence                                                  |
| ----------------------------------------------------------------------------------- | ---------------------------------- | -------------------------------------------------------------------- |
| Simple Pi → extension → real Deep Agent path                                        | S0                                 | Live POC with backend-path negative control                          |
| Natural-language task type, constraints, questions, source-grounded proposal        | S1                                 | S1-T1 through S1-T6                                                  |
| Exact approval, amendments, permissions, stale/duplicate rejection                  | S2                                 | S2-T1 through S2-T6                                                  |
| User checkout preservation, exact source, sandbox, credentials, tools/dependencies  | S3                                 | S3-T1 through S3-T3 and S3-T8                                        |
| Durable execution independent of UI; pause/cancel/steer/recovery                    | S3; shared lifecycle               | S3-T4 through S3-T7                                                  |
| Deterministic verification, independent review, bounded repairs, honest deliverable | S4                                 | S4-T1 through S4-T8                                                  |
| Investigation/fix/feature/refactor processes and curated guidance                   | S5A/S5B                            | S5-T1 and S5-T2                                                      |
| DAG, specialist delegation, controlled integration, selective invalidation          | S5C                                | S5-T3 through S5-T5                                                  |
| Testable improvement, model routing, cost/quality evidence                          | S5D; testing section               | S5-T6; versioned held-out evaluation                                 |
| Selected issue, authenticated trigger/approval, duplicate-safe input                | S6A                                | Valid and adversarial GitHub intake exercise                         |
| Scalable execution, durable artifacts, cross-host recovery                          | S6B                                | Redelivery, lease, restart, backup/restore exercises                 |
| Real custom VPC execution and tenant/resource isolation                             | S6C                                | Remote task and isolation/quota failures                             |
| Verified result, correct Git ancestry, one PR, actual CI trigger                    | S6D                                | Publication and ambiguous-outcome reconciliation exercise            |
| Fresh GitHub CI and pre-merge staging validation                                    | S6E                                | Current artifact deploy; failed/stale/colliding deployment exercises |
| Human merge, rejection, cleanup, operational readiness                              | S6F                                | Manual merge and close/reject lifecycle exercises                    |
| Schema/API compatibility, telemetry/privacy, evidence retention                     | Shared contracts; testing; S6B/S6F | Migration, event replay, redaction, restore and cleanup checks       |

### Recommended development order from the current checkout

1. **Maintain the approved local release:** S1–S4 profile/compatibility/oracle/diagnostic gaps and local S5 playbooks/guidance/DAG/evaluation plumbing are implemented. Preserve dated regression and live evidence in LOCAL_S5_EVIDENCE.md.
2. **Broaden local evidence before broad release claims:** approve representative real-repository tasks and any additional stack profile independently. Measure repeated live baseline/candidate quality, provider cost and human intervention before changing defaults.
3. **Add optional S5 integrations only where useful:** external skills/Pi packages and selective steering need their own bounded approval, compatibility tests and evaluation. Existing original guidance does not establish third-party package compatibility.
4. **Keep one worker as default:** declared coupled fixtures establish scheduling behavior; scripted speed does not establish production gain. Review a repeated live comparison against the predeclared thresholds before changing routing/parallelism.
5. **Design S6A–S6C interfaces together, implement incrementally:** choose the remote decisions, prove intake/authority and queue recovery with fixtures, then provision an explicitly approved isolated pilot. S6 does not depend on installing all optional S5 skills.
6. **Complete S6D–S6F as a connected release:** real publication → actual CI → staging before merge → human disposition → cleanup. Do not label a partial remote worker demonstration as the completed factory.

A handoff for any increment uses the existing ID and includes: current evidence, exact proposed behavior/diff scope, dependencies/decisions, artifact/schema changes, authority implications, normal and failure flows, tests, migration/recovery, explicit exclusions, and an exit gate. Keep detailed slice scope in this file so later handoffs reference it rather than creating divergent roadmaps.

## Evidence and document maintenance

Primary repository references inspected for this plan:

- [POC README](../../tools/pi-deepagent-poc/README.md) and [POC evidence](../../tools/pi-deepagent-poc/EVIDENCE.md).
- [Runtime README](../../tools/shinobi-agent/README.md), [recorded local validation](../../tools/shinobi-agent/EVIDENCE.md), [request/proposal contracts](../../tools/shinobi-agent/contracts.py), and [execution contracts](../../tools/shinobi-agent/execution_contracts.py).

Historical design inputs were `/tmp/shinobi-product-blueprint-2026-10-10.md`, `/tmp/shinobi-showdown-codex-handoff-2026-10-10.md`, and `/tmp/shinobi-pi-deepagent-poc-handoff-2026-10-10.md`. Their relevant product direction, processes, boundaries, and open decisions are consolidated here so the development plan does not depend on those temporary files surviving. Older application/game requirements under `docs/requirements/` describe a different scope; they are not a substitute for this agent-runtime roadmap.

External GitHub behavior was checked against official documentation on 2026-10-10 and linked beside the relevant S6 requirements. Recheck it during implementation, particularly token-trigger behavior, environment-plan limitations, and workflow security. Historical skill/package inspirations have not been represented as installed or currently compatible integrations.

When work lands, update the status table, relevant slice's remaining work, decision register, and evidence references together. Record which baseline was validated. Preserve the S0–S6 identifiers, distinguish implemented from validated and broadly evaluated, and keep unresolved limitations visible. This file is the consolidated roadmap; source code and dated evidence determine what actually exists.
