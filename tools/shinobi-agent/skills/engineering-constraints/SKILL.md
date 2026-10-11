---
name: engineering-constraints
description: Bind relevant engineering quality requirements to executable checks and explicit measurable thresholds without weakening the quality bar.
---

Read the project's existing quality rules, scripts, tests and constraint files.
Select dimensions relevant to this task: compatibility, types, architecture,
security, performance or accessibility. Do not add every possible check to a
small change. Explain the selection in `guidance_reason`.

Record enforceable requirements in `engineering.quality_constraints`: a stable
`id`, the concrete `requirement`, and approved `check_ids`. An ordinary pass/fail
check can enforce a type or lint requirement. For a numeric budget, add a
`measurements` entry to the check: `key`, `operator` (`le`, `ge`, `eq`), finite
numeric `threshold`, and `unit`. The harness must emit a single JSON object to
stdout with that numeric key; send diagnostic logs to stderr. The controller
records the observed value and compares it with the approved threshold. Missing,
duplicate, boolean or non-finite observations do not satisfy a measurement.

Thresholds require a stated reason: an existing project rule, explicit user
direction, or a recorded baseline. Never invent a benchmark or treat an example
threshold as a universal standard. Account for noise and units before proposing
a performance budget. If a check cannot run in the supported environment, state
the missing capability; do not claim the dimension is enforced.

Implement in verifiable increments. Preserve protected checks and expectations.
Do not lower a threshold, skip tests, add suppressions, or replace a real surface
with a proxy to obtain green results. If the agreed requirement cannot be met,
report the cause and request an amendment. Reviewers must inspect both the
implementation and how the checks establish the claimed quality.

This is original Shinobi guidance, MIT licensed. Design reference:
[Osmani's constraint-driven development](https://github.com/addyosmani/agent-skills/blob/main/skills/constraint-driven-development/SKILL.md).
External commands and default thresholds from that collection are not adopted.
