# Choosing test doubles

Prefer real in-process collaborators when deterministic and inexpensive. Isolate an external boundary when the contract explicitly permits it and the real dependency is unavailable or unsuitable for the test. Mock the boundary, not internal implementation details.

State what the double omits: transport, authorization, persistence, ordering, timing or external side effects. Add separate integration verification for those obligations when supported. A unit test with a mock is not evidence that the real application path works.

Avoid assertions about private call order unless ordering itself is a required public effect. Preserve realistic errors and independently specified responses. Do not move the boundary inward merely to make a failing test pass.
