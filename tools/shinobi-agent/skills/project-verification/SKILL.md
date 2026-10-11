---
name: project-verification
description: Design executable checks that exercise the requested application behavior and preserve independently captured evidence.
---

Discover the actual surface: public library calls, CLI input/output, API requests,
or UI interaction. Reuse committed harnesses and documented commands. Identify
runtime dependencies, fixtures, isolation, startup/readiness, teardown, and the
observable state that proves the requested behavior. Record limitations explicitly.

Express verification as exact approved `checks` with bounded timeouts and protected
inputs. Put any startup, exercise and teardown inside a single supported harness;
checks must finish within their timeout. Protect the harness and its expected
results. Use inline Python assertions when the existing profile supports the
behavior without adding dependencies. A new reusable harness needs approved
owned paths; a harness that is not yet committed cannot be silently selected as a
protected baseline input. Propose a separate preparation contract when necessary.

The current execution profile has no network, host dependencies, browser service,
or dependency installation. Do not claim UI/server verification is available just
because a command can be described. Report an unsupported environment instead of
substituting a mock and calling it equivalent. Do not start unowned processes.

For a bug, capture the original symptom on the baseline and exercise the same path
on the candidate. For a refactor, require a passing baseline characterization.
When adding tests is appropriate, use a focused failing behavior test before the
fix and repeat it afterward. Worker checks are advisory; only controller checks
against the integrated artifact can satisfy delivery gates.

Map each acceptance criterion to the checks and expected observation. Inspect
both action and outcome, including relevant side effects. Distinguish real
execution, scripted model generation, mocks, source reasoning, and unrun checks.
Keep unsupported cases in `limitations`. Missing or stale evidence blocks a pass.

This is original Shinobi guidance, MIT licensed. Design reference:
[pstack's verification-skill generator](https://github.com/cursor/plugins/blob/main/pstack/skills/create-verification-skill/SKILL.md).
No Cursor-specific tools or permissions are inherited.
