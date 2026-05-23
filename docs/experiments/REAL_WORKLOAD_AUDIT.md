# v0.9.1.1 Real Workload Audit

## 1. Why This Audit Exists

v0.9.1 reported xlarge completion, but the recorded runtime was too small for a real 50k / 12k / 15k sample workload across multiple seeds, cross-process reload, baseline, and ablation evaluation. v0.9.1.1 audits whether those results came from real per-sample execution or harness/probe summary paths.

## 2. What Counts as Real Workload

- dataset samples actually iterated;
- evaluation functions actually called per sample or per batch with sample counters;
- cross-process reload actually started a child process;
- baselines actually evaluated on samples;
- ablations actually changed config and reran the relevant path;
- wall-clock and runtime counters are plausible for the reported sample count.

## 3. What Counts as Harness / Probe Only

- precomputed metrics;
- synthetic metric summaries;
- no real dataset iteration;
- fixed counters not tied to actual samples;
- baseline / ablation records generated without execution;
- cross-process reload marked true without subprocess evidence.

## 4. Non-Claims

This audit does not claim stable convergence, solved OOD, solved arithmetic, same-size LLM advantage, safe real promotion, or production readiness.
