---
name: quality-constraints
description: 'Establish relevant measurable project quality requirements and detect weakening of the checks used to enforce them.'
---

# Quality constraints

Start from existing project constraints, scripts, tests and baselines. Select the dimensions implicated by this task: behavior, compatibility, types, architecture, security, accessibility or measured performance. Do not install a new quality stack or apply arbitrary numerical targets by default.

1. For each constraint, state its rationale and the exact available check. A threshold comes from accepted requirements, existing policy or a measured baseline, with units and noise considerations.
2. Record `engineering.quality_constraints` with IDs, requirements and approved check IDs. For numeric checks, use the runtime's measurement schema and an unambiguous finite observation; a declared budget without an executable measurement remains unverified.
3. Run or inspect the baseline as permitted and distinguish pre-existing failures from regressions. Unsupported tools or environments are capability gaps, not reasons to claim equivalent proxy coverage.
4. Implement a small slice, check the affected constraints, then review the diff of both production code and verification inputs.
5. Detect attempts to lower the bar: deleted assertions, skipped tests, exclusions, broad suppressions, loosened thresholds, reduced discovery, hard-coded observations or replacement of a real boundary with a mock. A green command after such a change may prove less.
6. If a check itself is wrong, preserve its evidence and route the test-design decision for explicit correction. Do not weaken protected expectations during a product repair.

Completion means the relevant constraints have evidence on the candidate, or the remaining limitations are explicit. Establishing the quality bar is occasional setup; a task reuses it and adds only justified requirements. A command's success does not alone establish that its assertions are adequate.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
