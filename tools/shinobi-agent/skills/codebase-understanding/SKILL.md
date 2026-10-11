---
name: codebase-understanding
description: 'Trace an existing behavior from its public entry point through ownership, state changes and observable results before planning or reviewing it.'
---

# Codebase understanding

Start with the exact question or behavior to explain. Establish the repository revision and source availability. Search for entry points and tests, then follow the relevant runtime path instead of inventorying every folder.

1. Identify the caller, boundary validation, controlling decisions, state changes and returned or emitted result. Trace asynchronous handoffs and error paths that matter to the question.
2. Locate ownership: who creates and disposes resources, authorizes actions, stores state, retries work and handles failure? Distinguish declarations from the code that actually executes them.
3. Inspect tests and configuration that establish the behavior. A symbol name or comment alone does not establish a runtime guarantee. Note version or feature-flag conditions.
4. Explain the flow with file/line citations and a small concrete example. Separate observed source behavior from a hypothesis requiring execution. Include the uncertainty that could change a plan.
5. For a change request, identify extension points, existing conventions and consumer obligations. Do not start redesigning merely because a different architecture is possible.

Output: a focused behavior map, decisive evidence, affected boundaries and unknowns. Workers receive the relevant original requirement alongside this map. If the coordinator cannot execute a needed experiment, state that limitation and propose a bounded diagnostic task rather than report an unobserved result.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
