---
name: behavior-tdd
description: 'Implement one accepted behavior with a sensitive failing check and the smallest change that makes that behavior pass.'
---

# Behavior tdd

Read the assignment, acceptance scenarios, public test boundary and existing tests. Consult [test design](references/tests.md) for assertion choices and [test doubles](references/mocking.md) for isolation decisions.

1. Choose one behavior, not a bulk test suite against an imagined design. Derive the expected result independently from the requirement; do not compute it with the same algorithm under test.
2. Establish red on the relevant baseline. The failure must demonstrate the missing behavior, not invalid syntax, a broken fixture, import failure or unavailable dependency. If the behavior already holds, preserve that characterization and reconsider whether a change is needed.
3. Implement the smallest coherent change satisfying the scenario. Test through public behavior and stable boundaries rather than private call sequences or incidental structure.
4. Run the same approved check and inspect green. Include relevant failure/boundary cases one at a time. Repeat for the next behavior only after the current cycle is understood.
5. Preserve existing and admitted test expectations. A product repair cannot delete, skip or loosen the failing assertion. A mistaken oracle needs a separate test-design correction.

Shinobi integration: new regression tests may require a separately owned test-only task, demonstrated behavioral failure, independent admission and frozen content before implementation. Existing protected tests can provide red without a new test file. Work within those available operations; do not edit protected tests to imitate a textbook loop.

Keep refactoring outside the active red-green cycle. After behavior is green, use separately scoped `code-simplification` if warranted. Output the scenario, observed red/green evidence and remaining coverage gaps; writing a test without executing it is not a completed cycle.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
