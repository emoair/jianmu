# v0.9.3.2 Non-Periodic Arithmetic Rerun

v0.9.3.2 exists because the v0.9.3 arithmetic probe was downgraded by
v0.9.3.1. The audit found that the reported 0.95 arithmetic signal could be
explained by a deterministic index-period rule, fixed metric values, or
summary-only aggregation without enough per-sample candidate provenance.

This version reruns the arithmetic probe on the audited v0.9.2 arithmetic
curriculum with a narrower purpose: determine whether JianMu still shows an
arithmetic candidate-space improvement after removing periodic success
schedules and fixed metric paths.

## Forbidden Periodic Rule

A forbidden periodic rule is any candidate or success path that depends on
sample order rather than sample content and router/root state. Examples include
index-period success masks, fixed 0.95 caps, precomputed success schedules, and
summary metrics presented as per-sample measurements.

## Per-Sample Candidate Trace

Each evaluated sample emits a candidate trace record with hashed sample and
candidate identifiers, candidate count, beam size, candidate-hit status,
correct-output-in-beam status, top-1 status, and explicit flags for periodic,
fixed, and summary metric paths. The trace also records whether expected output
or target IR was accessed before candidate generation.

## Real Arithmetic Signal

A real signal requires per-sample aggregation, no periodic rule, no fixed metric
assignment, no summary-only metric path, no forbidden-field leakage, preserved
boundary behavior, and a baseline/ablation gap that is computed from sample
records.

## Non-Signals

The following do not count as arithmetic evidence:

- fixed 0.95 success rates;
- index-period success rules;
- summary-only metrics;
- candidate generation that reads expected output or target IR;
- boundary improvement caused by a hand-written keyword gate.

## Non-Claims

This version does not claim solved arithmetic, stable convergence, solved OOD,
general program synthesis, same-size LLM advantage, safe real promotion, or
production readiness.
