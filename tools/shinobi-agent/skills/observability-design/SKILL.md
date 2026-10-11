---
name: observability-design
description: 'Make an asynchronous workflow or service diagnosable with purposeful signals tied to state transitions and failure ownership.'
---

# Observability design

Identify the operational questions that cannot currently be answered: who owns the work, which stage failed, whether progress is stale, or which dependency dominates latency.

1. Map the relevant execution lifecycle and failure paths. Choose logs, metrics or traces that distinguish those states without duplicating every internal event.
2. Define correlation identifiers, meaningful transitions, bounded labels and redaction. Do not record secrets, unnecessary payloads or unbounded high-cardinality values.
3. Instrument at ownership boundaries and include error cause, outcome and duration where useful. Distinguish attempted, accepted and completed operations.
4. Exercise a success, failure and interruption scenario in the approved environment. Verify the signal reaches its intended destination and supports diagnosis; adding a logging call is not sufficient.
5. Document signal semantics and limitations. Avoid alerts with no actionable owner or condition.

Output: targeted instrumentation and observed evidence. Choosing or provisioning a hosted telemetry system is a separate decision; no external export is implied by this skill.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
