# Shinobi-owned engineering skills

Shinobi maintains these procedures locally. We copied and adapted selected
mechanisms from the reviewed skill collections, not their packages or entire
repositories. The skill bodies are operating instructions, not wrappers that
require reading an upstream document. Local changes need no upstream update,
fetch, installation, byte equality or synchronization.

Each adapted skill retains its MIT notice in `LICENSE` and source ancestry in
`provenance.json`. Those historical identifiers provide attribution. The runtime
hashes the **current local content** of selected skills and resources into the
reviewed contract; a local change needs a fresh contract before it governs an
existing task. This protects the user's accepted instructions without pinning
Shinobi's development to someone else's repository.

## Selection and use

The registered library has 44 entries: 20 primary procedures, six maintenance
procedures, 14 specialists, one opt-in autonomy procedure and three compatibility
guides. Availability is not a 44-step lifecycle. `skills/catalog.json` is the
registration source; the coordinator sees descriptions and reads relevant bodies
through `read_engineering_skill`. No external skill discovery is enabled.

- A clear request skips requirements discovery; an ambiguous one uses discovery,
  interview and domain modeling. Those dependencies are bound together when
  discovery is selected.
- The coordinator selects additional planning, source-grounding, handoff and
  specialist procedures for the actual task and explains its choices.
- Execution defaults include context preservation, decision evidence and separate
  specification/quality review. Changes add incremental implementation, quality
  constraints and failure correction; features and fixes add behavior TDD; fixes
  add diagnosis. Investigations do not receive an implementation/TDD workflow.
- Multiple work items add dependency execution. The controller still owns actual
  workers, integration and budgets; no imported skill launches another runtime.
- Verification-recipe creation is selected only when a recipe is missing or needs
  repair. Ordinary tasks reuse a proven project recipe. The existing
  `project-verification` guide remains selected for engineering check mapping.
- Maintenance is selected for an explicitly scoped maintenance task, not after
  every edit. It cannot change a running task's governing skills or checks.
- `bounded-autonomy` is added for `within_contract`. Merely reading or selecting
  it does not activate autonomy. The first exact contract still needs approval.

Selected bodies go to compatible execution roles; selected resources remain
available through the read tool. The contract contains the accepted selection.
Unselected skills cannot be loaded through the execution skill tool. A skill
provides a procedure, not missing tools or permission to expand the task.

## Procedural choices

- One specification and one dependency graph remain authoritative. The adapted
  specification procedure uses testable outcomes and scope; the planning procedure
  uses complete verifiable slices and true producer/consumer edges.
- Worker context retains original requirement text, constraints, decisions and
  actual evidence. Handoffs must be reconciled with current state.
- TDD uses one behavioral red-green cycle at a time. Refactoring is a separately
  scoped activity after green, not a conflicting second cycle.
- Requirements review and engineering review have different jobs. A green suite
  or a quality pass cannot substitute for checking the requested outcome.
- Failures are classified before repair. Recurring structural/process correction
  is separate maintenance rather than another name for an implementation retry.
- No fixed reviewer count, self-assigned confidence target, blanket comment
  deletion, implicit external publication, model fallback or upstream setup command
  is imported.

## Current boundaries

The catalogue is implemented; model selection/compliance quality is not established
by structural validation or scripted tests. Some specialist procedures can plan
work that the current offline Linux profile cannot execute, notably browser and
network service verification. They must report the capability gap, not substitute
unit tests and claim a real UI run. Existing worker/model limits and protected test
admission remain unchanged.

The earlier live corpus result remains 0/7 before execution. This skill change
does not implement the separately proposed coordinator validation-feedback loop
or erase that evidence. Representative live evaluation remains necessary before
claiming improved autonomous engineering quality.

## Local catalogue

### Primary

| Local skill                                                              | Use                                                                                                                                                |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| [requirements-discovery](skills/requirements-discovery/SKILL.md)         | Coordinate requirements discovery when intent or terminology is unresolved; reuse established answers for a clear task.                            |
| [requirements-interview](skills/requirements-interview/SKILL.md)         | Resolve material product choices in dependency order and distinguish user requirements from researched facts and assumptions.                      |
| [domain-modeling](skills/domain-modeling/SKILL.md)                       | Resolve ambiguous domain terms, identities, relationships and invariants when those distinctions affect the requested behavior.                    |
| [codebase-understanding](skills/codebase-understanding/SKILL.md)         | Trace an existing behavior from its public entry point through ownership, state changes and observable results before planning or reviewing it.    |
| [technical-research](skills/technical-research/SKILL.md)                 | Investigate a consequential technical unknown with primary evidence, competing explanations and a recommendation scoped to the user’s constraints. |
| [specification](skills/specification/SKILL.md)                           | Turn confirmed requirements into one testable specification with explicit scope, constraints and unresolved decisions.                             |
| [task-decomposition](skills/task-decomposition/SKILL.md)                 | Split an accepted specification into independently verifiable slices with ownership, acceptance and real dependency edges.                         |
| [dependency-execution](skills/dependency-execution/SKILL.md)             | Coordinate multiple approved dependent tasks using a ready frontier, isolated workers and verification of the integrated specification.            |
| [context-management](skills/context-management/SKILL.md)                 | Preserve original requirements, decisions and reliable evidence across task boundaries while keeping each worker context focused.                  |
| [context-handoff](skills/context-handoff/SKILL.md)                       | Prepare a restartable handoff at interruption or ownership transfer, including actual state, unresolved decisions and next verification.           |
| [source-grounding](skills/source-grounding/SKILL.md)                     | Resolve version-sensitive API or framework choices from installed code and primary documentation instead of remembered examples.                   |
| [quality-constraints](skills/quality-constraints/SKILL.md)               | Establish relevant measurable project quality requirements and detect weakening of the checks used to enforce them.                                |
| [incremental-implementation](skills/incremental-implementation/SKILL.md) | Implement one verifiable behavior slice at a time and re-ground the remaining plan when observed results contradict assumptions.                   |
| [behavior-tdd](skills/behavior-tdd/SKILL.md)                             | Implement one accepted behavior with a sensitive failing check and the smallest change that makes that behavior pass.                              |
| [decision-review](skills/decision-review/SKILL.md)                       | Challenge a consequential plan, interface or implementation decision with independent evidence before dependent work compounds a mistake.          |
| [failure-correction](skills/failure-correction/SKILL.md)                 | Classify a failed check or review, investigate its cause and return to the responsible stage instead of blindly patching or weakening tests.       |
| [application-verification](skills/application-verification/SKILL.md)     | Design and prove a project-local recipe for driving the real application when no adequate reusable verification procedure exists.                  |
| [specification-review](skills/specification-review/SKILL.md)             | Independently compare a plan or completed artifact with original requirements, keeping specification compliance separate from engineering quality. |
| [execution-evidence](skills/execution-evidence/SKILL.md)                 | Keep autonomous work reviewable by recording consequential decisions, evidence and unresolved outcomes as they occur.                              |
| [decision-documentation](skills/decision-documentation/SKILL.md)         | Update affected documentation and preserve consequential design decisions when a change alters supported behavior or future engineering choices.   |

### Maintenance

| Local skill                                                          | Use                                                                                                                                            |
| -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| [verification-maintenance](skills/verification-maintenance/SKILL.md) | Audit a project verification recipe against current source and live feature behavior when the app or harness has changed.                      |
| [workflow-retrospective](skills/workflow-retrospective/SKILL.md)     | Diagnose recurring workflow friction from actual run evidence and propose targeted environment or procedure improvements.                      |
| [structural-correction](skills/structural-correction/SKILL.md)       | Prevent an evidenced recurring mechanical error with a narrowly scoped structural change and demonstrate that it catches the original failure. |
| [skill-improvement](skills/skill-improvement/SKILL.md)               | Propose or apply an authorized skill revision based on demonstrated usage failures while preserving accepted decisions and counterexamples.    |
| [lesson-encoding](skills/lesson-encoding/SKILL.md)                   | Decide whether a repeated lesson belongs in executable structure, a focused skill step or contextual documentation.                            |
| [skill-authoring](skills/skill-authoring/SKILL.md)                   | Author or revise a focused Shinobi skill with discoverable triggers, useful procedures, local references and observable completion conditions. |

### Specialist

| Local skill                                                  | Use                                                                                                                                                       |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [bug-diagnosis](skills/bug-diagnosis/SKILL.md)               | Diagnose stubborn or intermittent failures with a sensitive reproducer, competing hypotheses and discriminating observations.                             |
| [quality-review](skills/quality-review/SKILL.md)             | Review the actual candidate for correctness, security, maintainability, performance and testing without substituting quality for requirements validation. |
| [adversarial-review](skills/adversarial-review/SKILL.md)     | Adjudicate a contested change using independent reviews and concrete evidence when additional perspectives justify their cost.                            |
| [initiative-planning](skills/initiative-planning/SKILL.md)   | Structure a large unclear initiative around dependent decisions before committing to implementation tickets.                                              |
| [impact-analysis](skills/impact-analysis/SKILL.md)           | Trace the behavioral impact of a shared interface or state change beyond direct textual callers.                                                          |
| [interface-design](skills/interface-design/SKILL.md)         | Design a changed public or shared interface from consumer behavior, explicit invariants and compatibility obligations.                                    |
| [security-review](skills/security-review/SKILL.md)           | Assess trust boundaries and abuse cases for changes involving authorization, untrusted input, secrets or tool execution.                                  |
| [performance-analysis](skills/performance-analysis/SKILL.md) | Investigate a measured performance problem using comparable baselines, profiling and correctness-preserving experiments.                                  |
| [migration-planning](skills/migration-planning/SKILL.md)     | Plan compatibility-preserving changes to shared APIs or persisted data using consumer inventory, staged cutover and recovery.                             |
| [browser-verification](skills/browser-verification/SKILL.md) | Plan or execute browser-visible verification with real user interactions and evidence when an authorized browser environment exists.                      |
| [observability-design](skills/observability-design/SKILL.md) | Make an asynchronous workflow or service diagnosable with purposeful signals tied to state transitions and failure ownership.                             |
| [code-simplification](skills/code-simplification/SKILL.md)   | Simplify a verified implementation while preserving behavior, public contracts and independently established checks.                                      |
| [design-alternatives](skills/design-alternatives/SKILL.md)   | Compare materially different viable designs for a consequential decision using the same requirements and explicit evaluation criteria.                    |
| [independent-coverage](skills/independent-coverage/SKILL.md) | Partition a broad review or verification task into independent coverage responsibilities with explicit methods and evidence.                              |

### Opt-in

| Local skill                                          | Use                                                                                                                                               |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| [bounded-autonomy](skills/bounded-autonomy/SKILL.md) | Continue routine decisions and bounded repairs without repeated consent when the user explicitly selected autonomy in the reviewed task contract. |

### Compatibility

| Local skill                                                              | Use                                                                                                                                        |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| [requirements-to-acceptance](skills/requirements-to-acceptance/SKILL.md) | Compatibility guide for the existing engineering acceptance-to-check schema; prefer the focused requirements and specification skills.     |
| [project-verification](skills/project-verification/SKILL.md)             | Compatibility guide for executing approved project checks and recording their evidence; reuse an established project verification recipe.  |
| [engineering-constraints](skills/engineering-constraints/SKILL.md)       | Compatibility guide for the existing numeric quality measurement schema; prefer quality-constraints for selecting the project quality bar. |

## Maintenance and validation

Edit the local procedure and only its necessary references. Update catalogue
metadata when selection criteria change. Keep source ancestry as historical
attribution; do not rewrite source hashes to pretend local text is unchanged
upstream. Preserve the applicable notices in distributions.

Validate frontmatter and local links, exercise registration and selection, and
verify that local edits invalidate an existing contract while a fresh contract
accepts them. For consequential procedural changes, evaluate realistic behavior
with the actual model and report results separately from scripted control tests.
The library does not automatically install helpers, update from GitHub or publish
changes back to its source collections.

## Validation of this revision

The [validation record](SKILLS_EVIDENCE.md) records 44 valid entrypoints, 88 Python
tests, 11 bridge tests, both scripted Pi integration checks, typecheck, lint and
format checks. These establish local loading, selection and execution boundaries;
no live model quality improvement is claimed.
