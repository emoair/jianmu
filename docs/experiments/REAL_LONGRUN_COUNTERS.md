# v0.9.1.2 Real Longrun With Mandatory Counters

## 1. Why v0.9.1.2 Exists

v0.9.1 was audited by v0.9.1.1 as harness/probe summary evidence rather than verified real xlarge workload evidence. v0.9.1.1 also showed that the tracing infrastructure can record a small real-mini rerun with per-sample counters. v0.9.1.2 therefore performs real per-sample longrun validation with mandatory counters, workload traces, wall-clock profiling, cross-process child traces, and real baseline/ablation execution traces.

## 2. What Counts As Completed

A mode can be marked completed only when actual sample iteration is recorded, free-beam evaluation call counts are greater than zero, the cross-process child evaluation count is greater than zero, completed baseline/ablation rows have actual sample counts, wall-clock runtime is positive, counters match reported counts or document partial reasons, and trace files are emitted.

If reported counts are positive but actual counts are zero, the mode is invalid. If runtime is implausibly small for the reported sample count, the result is suspicious and cannot be promoted to a strong real-longrun claim without explanation.

## 3. What Cannot Be Claimed

This version does not claim stable convergence, solved OOD, solved arithmetic, same-size LLM advantage, safe real promotion, production readiness, AGI, or Transformer replacement.
