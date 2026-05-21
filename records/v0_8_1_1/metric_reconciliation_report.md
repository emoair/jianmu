# Overnight Metric Reconciliation & XLarge Reproduction（过夜指标口径校验与 xlarge 复验）

## Pytest Repair（测试修复）
- Fixed the mixed C-keyword generation path exposed by `test_negation_detector_does_not_trigger_on_fenbie`.

## Metric Inconsistency Audit（指标不一致审计）
- metric_consistency_passed: True
- inconsistency_count: 0
- unresolved_issues: []

## Split Diagnostics（切分诊断）
- reason_for_limit_mismatch: dataset_capacity
- requested/actual train: 3000 / 2200
- requested/actual eval: 1000 / 600
- requested/actual ood: 500 / 200

## XLarge Same-Seed Reproduction（xlarge 同 seed 复验）
- global_correct_targetir_in_beam_rate: 0.8167
- candidate_space_failure_rate: 0.1833

## XLarge Alt-Seed / Light Reproduction（xlarge 异 seed / light 复验）
- global_correct_targetir_in_beam_rate: 1.0
- candidate_space_failure_rate: 0.0

## Guard Metric Baseline Fix（守卫基线修复）
- guard_candidate_accepted_count: 2
- global_beam_after_guard: 0.8167

## Root Lifecycle Metric Clarification（根生命周期指标澄清）
- cumulative_nourished_event_count: 4548
- final_nourished_root_count: 0

## Updated Mainline Judgment（更新主线判断）
- xlarge_08167_conclusion: confirmed

## Non-Claims（非主张）
- This does not prove stable convergence.
- This does not prove general program synthesis.
- This does not prove solved arithmetic.
- This does not prove AGI, Transformer replacement, or advantage over same-size LLM.
