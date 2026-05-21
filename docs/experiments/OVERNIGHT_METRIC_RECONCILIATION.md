# Overnight Metric Reconciliation（过夜指标口径校验）

## 1. Why Reconciliation（为什么做口径校验）

v0.8.1 overnight produced a strong xlarge signal: global_correct_targetir_in_beam_rate（全局正确 TargetIR 在束内率） reached 0.8167. However, the run also exposed a pytest failure, sample-count mismatch, possible guard baseline reuse, and before/after metric ambiguity. v0.8.1.1 therefore treats 0.8167 as an unverified positive signal（未验证正信号） until reproduced with consistent metrics.

## 2. Metric Definitions（指标定义）

- global_correct_targetir_in_beam_rate（全局正确 TargetIR 在束内率）: free global beam evaluator result for a named run and split.
- candidate_space_failure_rate（候选空间失败率）: 1 - correct_targetir_in_beam_rate under the same evaluator.
- global_correct_targetir_in_beam_rate_before_shadow（影子前全局正确 TargetIR 在束内率）: baseline before Shadow Promotion（影子晋升）.
- global_correct_targetir_in_beam_rate_after_shadow（影子后全局正确 TargetIR 在束内率）: result after shadow-only local changes.
- global_correct_targetir_in_beam_rate_before_guard（守卫前全局正确 TargetIR 在束内率）: current-mode guard baseline.
- global_correct_targetir_in_beam_rate_after_guard（守卫后全局正确 TargetIR 在束内率）: current-mode guard result.
- candidate_space_failure_rate_before_guard（守卫前候选空间失败率） and candidate_space_failure_rate_after_guard（守卫后候选空间失败率） must use the same evaluator.
- ood_false_accept_before_guard（守卫前分布外误接收率） and ood_false_accept_after_guard（守卫后分布外误接收率） must use the same OOD split.
- arithmetic_supported_retention_before_guard（守卫前算术支持保留率） and arithmetic_supported_retention_after_guard（守卫后算术支持保留率） must use the same supported arithmetic split.

The same metric name must not be reused across different evaluator names or baseline modes.

## 3. Reproduction Policy（复验策略）

The reproduction policy requires:

- xlarge same-seed repeat（xlarge 同 seed 复验）.
- xlarge alternate-seed repeat（xlarge 异 seed 复验） or xlarge-light alternate-seed（xlarge-light 异 seed） when bounded runtime is needed.
- sample split hashes（样本切分哈希）.
- run_id（运行编号）.
- evaluator_name（评测器名称）.
- guard baseline source（守卫基线来源）.

## 4. Non-Claims（非主张）

This work does not claim stable convergence, general program synthesis, solved arithmetic, AGI, Transformer replacement, or advantage over same-size LLM.
