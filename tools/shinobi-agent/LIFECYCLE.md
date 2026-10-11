# Requirements-grounded engineering lifecycle

The controller retains original user turns, a versioned requirements record,
acceptance scenarios, task ownership, and executable checks. A model's summary
cannot replace those records. An executable contract requires a complete lifecycle
plan and an independent planning review. Exact-hash approval remains mandatory.

## Operator flow

1. Discuss the task. The coordinator inspects the committed repository and reads
   the relevant stage skills. It can retain partial `Outcome.requirements` while
   asking material questions.
2. Inspect the proposed `lifecycle` record. Requirements identify their original
   `source_turn` and verbatim `source_quote`; interpretations are labelled
   `inference`. Changed records increment `revision`; removed IDs require a
   `supersedes` rationale. Decisions record dependencies, choices and rationale.
3. Request `/shinobi-contract`. Unresolved questions, invalid lineage, orphan
   tasks or scenarios, and unsupported IDs block compilation. A separate model
   invocation reviews the original instructions, plan, verification adequacy and
   feasibility. Its role model is the contract's configured reviewer.
4. A failed planning review creates no executable contract. Its classified
   findings are persisted and supplied to the next conversation turn. Revise the
   proposal and request another contract.
5. Review the full resulting contract and `/shinobi-approve <hash>`. Optional
   `/shinobi-autonomy on` still drafts a contract and grants no authority itself.
6. Observe diagnosis, slice review, combined checks, quality review and final
   requirements validation. The local result includes these records and evidence.

Planning is read-only. It may inspect source but cannot run arbitrary experiments.
When diagnosis needs new instrumentation or an unavailable environment, propose
an appropriately bounded preparation/diagnostic contract. The offline Linux
profile has no browser service, network, host dependency mounts or installation.

## Shinobi-owned skills

The [local skill catalogue](SKILLS.md) replaces the earlier twelve upstream
adapters with independently maintained procedures. It contains 20 primary skills,
six maintenance skills, 14 specialists, one opt-in autonomy skill and three
compatibility guides. The coordinator selects applicable procedures; the library
is not a mandatory full workflow for every task.

`skills/catalog.json` registers local names, roles, categories and descriptions.
Skill bodies and their selected local references are operating instructions.
`provenance.json` records ancestry and `LICENSE` preserves attribution; neither
requires upstream access or unmodified upstream bytes. Full copied upstream
entrypoints and unused supporting resources have been removed.

The contract binds current local instructions and resource hashes. Local changes
are allowed, but existing approval does not silently authorize changed guidance.
The execution reader rejects unselected or changed resources. Selection grants
no extra tools, model calls, publication rights or execution permissions.

Requirements discovery, verification-recipe creation, contested review and
maintenance have distinct triggers. Execution defaults vary by task: investigation
and refactor do not force behavior TDD; multi-item plans add dependency execution;
opt-in autonomy adds its local procedure. See [selection rules](SKILLS.md#selection-and-use).
Reading a procedure is observable but is not proof of compliance.

## Lifecycle data

`lifecycle` contains:

- `requirements`: revision, requirement records, glossary, decisions,
  uncertainties and supersedes rationales. Requirement kinds are `behavior`,
  `invariant`, or `exclusion`.
- `scenarios`: stable IDs, requirement IDs, zero-based acceptance criterion,
  initial conditions, action, expected result, side effects, surface and check IDs.
- `assignments`: one per work item, with requirement and scenario IDs.
- `test_admissions`: optional test-only producers described below.
- `selection_reason`: why the selected procedure fits the task.

Every behavior and invariant needs a scenario; every scenario needs assigned
work; every work item must be justified by a scenario. Exclusions cannot justify
implementation. Decisions have an acyclic dependency graph. The existing work DAG,
ownership, interface and consumed-input checks still apply. Optional
`engineering.acceptance` mappings must agree with scenario checks.

Model-based planning review checks semantic adequacy, omitted requirements and
invented scope. Schema validation establishes identities and links, not truth.
Original instructions, inferred decisions and the review are visible in the exact
contract the user approves. Old contracts without lifecycle fields cannot execute;
they remain stored and need a fresh proposal, review and approval.

## New test admission

Existing protected test expectations remain immutable. A new regression test can
be introduced under an explicitly reviewed procedure in the first contract:

1. Declare an item owning only exact new test file paths. Those paths must not
   exist in the committed baseline. Declare its scenario/check IDs under
   `test_admissions`.
2. Make each implementation item for those scenarios depend on the test item.
   No other worker may own the test paths. Choose an exact approved command able
   to execute the new test; checks awaiting admission are explicitly deferred on
   the original baseline, never reported as passing.
3. The controller runs the new test against the candidate before dependent
   implementation. Each admission check must expose failing behavior. Syntax
   errors, missing modules and broken unittest harnesses cannot establish it.
4. An independent reviewer receives test source, original scenarios and captured
   failures. Only a passing review admits the test.
5. Admission records the test content/mode hashes with the integrated candidate
   transaction. Later workers cannot edit admitted paths. Resume, checkpoints and
   final delivery recheck the hashes.
6. The final integrated artifact must pass the same approved checks. Evidence
   retains the failing admission, test hashes, review and passing result.

A new test that already passes cannot use this regression-admission route. Use
existing characterization checks for behavior that already holds, or propose a
separate preparation task with the correct acceptance semantics. Changing an
existing protected expectation requires a separately reviewed contract, not an
exception inferred by a worker.

## Checkpoints and correction

Bug fixes require observed reproduction, a structured diagnosis and independent
review before implementation. Hypotheses must make predictions and name actual
observations. An inconclusive diagnosis requests amendment. An already-satisfied
claim cannot contradict a failing observed check.

Every worker receives its requirement/scenario slice, global invariants and
exclusions, relevant decisions and the approved contract. Before integration, a
fresh reviewer examines the work item and available localized evidence. Combined
checks remain explicitly deferred until all required items are integrated.

Independent quality review is followed by requirements validation against the
original instructions. Both are bound to the exact artifact. Validation cannot
be replaced by a quality pass. User acceptance and applying/publishing the patch
remain separate.

A failed check or review enters a correction assessment before a permitted
implementation repair. Findings classify implementation, diagnosis, plan,
test-design, environment or requirements problems. Implementation repairs use the
existing bounded retry allowance; other changes route to the appropriate
clarification/amendment or environment-blocked outcome. Admitted tests are retained
during implementation repair. Failures and earlier hypotheses remain recorded.
The run cannot modify its own governing skills or policy as a learning shortcut.

`adversarial_models` optionally selects up to two explicit, distinct models other
than the primary reviewer. Each receives fresh context and the same evidence.
Opinions are retained and provided to final validation. Any blocking opinion must
be resolved; voting cannot waive a gate. The default is an empty list and there
are no model fallbacks. These calls consume the approved model-call/time budget.

## Validation and limits

The [2026-10-11 evidence report](LIFECYCLE_EVIDENCE.md) records 84 Python tests,
11 bridge tests, both scripted Pi integration checks and 42/42 scripted evaluation
trials. The subsequent [live evaluation](LIFECYCLE_LIVE_EVIDENCE.md) completed
0/7 corpus cases, with all failures before execution, while the separate live
Pi integration check passed. Coordinator validation feedback and structured-output
handling remain reliability gaps.

Tests exercise missing lineage, fabricated origins, orphaned assignments,
unresolved decisions, rejected planning, incomplete review coverage, wrong-surface
validation, test-before-implementation ordering, immutable admitted tests, exact
approval, interruption, recovery and evidence identity. Scripted model output is
kept distinct from real sandbox/check/controller execution.

The workflow corpus includes a CLI scenario that checks process output and a
written receipt, alongside library, feature, refactor and diagnostic fixtures.
This is a supported stdlib application surface, not browser/UI validation or a
representative Angular/Rust application benchmark. Evaluation fingerprints include
the skill resources and lifecycle controller modules. Reports retain failures,
latency, model calls and unknown cost/intervention counts.

A live baseline/candidate comparison is required before claiming better model
quality. The repository's existing comparison measures one versus two workers;
it does not reconstruct the previous three-skill runtime as a historical baseline.
No such quality improvement is established by the scripted regression suite.
