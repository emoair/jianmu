# JianMu v0.8 Mainline Ledger Summary

This summary is a writing aid for the v0.8 technical report draft. It does not replace the original records and does not modify experimental data.

## v0.7.9 Colony Nutrient Activation（根群养分激活）

### 1. What it proved

- Local root colony lifecycle could be activated.
- Nourished, stable, starving, necrotic, and replacement root states became observable.
- Keep-local and shadow promotion scaffolds were usable without real promotion.

### 2. What it did not prove

- Global beam improvement.
- Stable convergence.
- Safe real promotion.
- General program synthesis.

### 3. New bottleneck

- Local lifecycle worked, but the global beam stayed flat.
- OOD false accept still required stronger guard accounting.

### 4. Paper relevance

- Medium-high. It supports the claim that Root Colony（根群） lifecycle mechanics are executable, but not that they solve routing globally.

### 5. Needs reproduction?

- Yes, especially under larger scale and more OOD slices.

## v0.8.0 Colony Scale Stress Probe（根群规模压力探针）

### 1. What it proved

- Scale improved supported global beam in bounded small/medium/large runs.
- Stable roots increased with scale.
- OOD toxicity did not improve automatically with scale.

### 2. What it did not prove

- Full or longrun completion.
- OOD robustness.
- Safe real promotion.
- General synthesis.

### 3. New bottleneck

- OOD toxicity and false accept remained high.
- Need to determine whether routing is scale-limited, OOD-limited, or resource-limited.

### 4. Paper relevance

- High. It provides the first clear scale-sensitive signal in the v0.8 line.

### 5. Needs reproduction?

- Yes. v0.8.1 and v0.8.1.1 were designed partly to reproduce and clarify this signal.

## v0.8.1 OOD Toxicity Long-Run Scale（分布外毒性长时规模）

### 1. What it proved

- Large mode completed.
- OOD false accept could be reduced from 0.335 to 0.235 by a rollback-safe guard candidate while arithmetic retention stayed 1.0.
- canonicalizer_made_it_look_supported was identified as a major false accept reason.

### 2. What it did not prove

- xlarge/full/longrun completion in the main v0.8.1 report.
- Stable OOD guard behavior across wider slices.
- Safe real promotion.

### 3. New bottleneck

- OOD guard must become canonicalization-aware.
- Runtime and checkpointing need to support larger-scale verification.

### 4. Paper relevance

- High for failure analysis and OOD taxonomy.

### 5. Needs reproduction?

- Yes. Guard effects and xlarge scale signal required metric reconciliation.

## v0.8.1 Overnight Longrun Probe（过夜长时探针）

### 1. What it proved

- It produced a strong xlarge signal: global beam 0.8167, candidate failure 0.1833.
- Guard candidate still reduced OOD false accept from 0.335 to 0.235 while arithmetic retention stayed 1.0.

### 2. What it did not prove

- The signal was not yet verified due to pytest failure, split mismatch, and guard baseline ambiguity.
- Full/longrun completion.
- Stable convergence.

### 3. New bottleneck

- Metric definitions and baseline accounting had to be reconciled before the signal could enter the paper draft.

### 4. Paper relevance

- Conditional. The numbers were promising but should not be cited as confirmed until v0.8.1.1 reconciliation.

### 5. Needs reproduction?

- Yes. Same-seed and alternate-seed/light reproduction were required.

## v0.8.1.1 Overnight Metric Reconciliation & XLarge Reproduction（过夜指标口径校验与 xlarge 复验）

### 1. What it proved

- xlarge strong signal was confirmed after metric reconciliation.
- metric_consistency_passed was true.
- inconsistency_count was 0.
- split mismatch was explained as dataset_capacity.
- xlarge same-seed global beam reached 0.8167 with candidate failure 0.1833.
- xlarge alt-seed/light global beam reached 1.0 with candidate failure 0.0.
- Guard baseline was fixed for the xlarge mode.

### 2. What it did not prove

- full/longrun completion.
- real promotion.
- advantage over same-size LLM.
- stable convergence.
- general program synthesis.
- solved arithmetic.

### 3. New bottleneck

- OOD pollution risk remains.
- Runtime scalability remains open.
- Same-size LLM / Transformer and heuristic baselines are missing.

### 4. Paper relevance

- High. The v0.8.1.1 result can enter the v0.8 technical report as a confirmed bounded-scale result.

### 5. Needs reproduction?

- Full/longrun and more seeds still need reproduction.
- Guard safety needs larger OOD slices and a canonicalization-aware guard.

## v0.8.7 Boundary Free-Beam Generalization Probe（边界自由束泛化探针）

### 1. What it proved

- No-label inference guard passed.
- Held-out leakage check passed.
- Boundary signal survived free-beam evaluation under probe criteria.
- Current supported retention remained 1.0.
- OOD false accept reached 0.0 under the tested slice.

### 2. What it did not prove

- Stable convergence.
- OOD solved.
- Full-scale generalization.
- Same-size LLM advantage.
- Safe real promotion.
- Real persisted router-state behavior.

### 3. New bottleneck

- Persisted router/root state replay.
- External OOD.
- Baseline comparison.

### 4. Paper relevance

- Very high. This is a key v0.8 result because it moves the v0.8.6 training-probe signal into a bounded no-label free-beam held-out probe.

### 5. Needs reproduction?

- Yes, with persisted state, external OOD, more seeds, and larger scale.
