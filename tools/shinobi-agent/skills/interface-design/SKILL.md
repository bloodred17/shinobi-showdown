---
name: interface-design
description: 'Design a changed public or shared interface from consumer behavior, explicit invariants and compatibility obligations.'
---

# Interface design

Read consumer use cases and current interfaces before choosing types or endpoints. State the operation's semantics independently of its transport.

1. Define valid inputs, output guarantees, errors, authorization, state changes and lifecycle ownership. Consider retries/idempotency or ordering only where the operation requires them.
2. Make invalid states difficult to express and keep responsibilities coherent. Prefer a simple contract over parameters that expose unrelated implementation details.
3. Walk a successful caller, invalid input, unavailable dependency and affected compatibility case. Resolve ambiguous semantics in the specification.
4. Identify existing consumers and whether rollout needs coexistence. Use `migration-planning` for public or persisted-format changes rather than immediate deletion by default.
5. Define contract tests through consumer-visible behavior with independently derived expectations. Document consequential choices and examples.

Output: the interface, invariants, compatibility plan and acceptance scenarios. Adding an API does not authorize a new service, dependency or external integration absent from the approved scope.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
