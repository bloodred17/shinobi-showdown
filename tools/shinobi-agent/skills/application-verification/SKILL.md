---
name: application-verification
description: 'Design and prove a project-local recipe for driving the real application when no adequate reusable verification procedure exists.'
---

# Application verification

This skill creates or repairs a verification recipe; ordinary tasks reuse the proven project recipe. Inspect the repository before asking the user how it works.

1. Discover the real user surface, documented launch/build command, environment needs, data/auth fixtures, existing harness, observable results and isolation strategy. Determine whether instances can coexist and who owns any running process.
2. Reuse an adequate harness. When a recipe is missing, draft it at an approved project-local path, with precise launch/readiness, a read-only doctor check, drive steps, evidence capture and cleanup. Use real selectors, command input or public routes rather than invented examples.
3. Build a feature map for the relevant user journeys and alternate entry points: initial state, how a user reaches the feature, harness actions, expected visible result, side effects and known gotchas. A convenient single entry point does not cover all mapped behavior.
4. Evidence must show action and outcome, including files, state or messages where relevant. Internal setters, test-only endpoints and mocks do not establish a real user path. Verify what a dry-run actually skips rather than trusting its name.
5. Execute launch, doctor, one mapped feature, evidence capture and cleanup end to end before calling the recipe proven. Cleanup only owned processes and scratch state; confirm evidence survives cleanup. Retain failed attempts and fix their cause before retrying.
6. Report unexercised features and route later drift to `verification-maintenance`.

Current Shinobi execution is offline Linux with approved bounded commands, no browser/network service or dependency installation. The coordinator can design but cannot execute recipes. A missing harness or unsupported surface needs an explicit preparation task or capability-gap report. Never call an unexecuted generated recipe verified, nor write into an unapproved skill directory.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
