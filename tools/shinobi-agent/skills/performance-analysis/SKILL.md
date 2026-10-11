---
name: performance-analysis
description: 'Investigate a measured performance problem using comparable baselines, profiling and correctness-preserving experiments.'
---

# Performance analysis

Define the user-visible performance objective, representative workload and environment. Establish a reproducible baseline before changing code.

1. Measure the relevant latency, throughput, memory or resource behavior with units, variance and workload details. Separate warm-up and setup costs where they affect comparison.
2. Profile to locate the actual bottleneck. Form a specific hypothesis and change one relevant factor at a time.
3. Compare baseline and candidate under equivalent inputs and conditions. Preserve correctness checks; caching away required work or reducing data quality is not a performance win.
4. Inspect distribution and regressions, not only the best run. Do not infer production scale from a tiny synthetic example.
5. Keep an improvement only when supported by evidence and compatible with the accepted constraints. If the environment cannot run the benchmark, report the gap.

Output: baseline, experiment, results, correctness evidence and limitations. Thresholds come from the approved objective or measured constraints, not fixed numbers imported from examples. No paid load generation or infrastructure provisioning is implied.

This is a Shinobi-maintained procedure. Attribution and retained license: [provenance.json](provenance.json), [LICENSE](LICENSE).
