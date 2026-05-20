# Wide-Beam Backtracking Search（宽束回溯搜索） Report

## Config（配置）
- mode: medium
- bounded_runtime_override（有界运行覆盖）: True
- Branch Beam Size（分支束宽）: 16
- proposals_per_layer（每层候选数）: 4
- stochastic_samples_per_layer（每层随机采样数）: 2
- confidence_noise（置信噪声）: 3.0
- clone_count_per_layer（每层克隆数）: 2
- perturbation_scale（扰动尺度）: 0.15
- Backtracking Window（回溯窗口）: 1
- backtracking_patience（回溯耐心）: 3
- population_per_layer（每层种群数量）: 32
- generations（训练代数）: 4
- train/eval/ood: 200 / 100 / 100

## Full Path Diagnostics（完整路径诊断）
- target_ir_exact_match_top1（Top1 TargetIR 精确匹配）: 0.0
- target_ir_exact_match_beam_oracle（束内 Oracle TargetIR 精确匹配）: 0.0
- beam_oracle_gap（束内上限差距）: 0.0
- correct_targetir_in_beam_rate（正确 TargetIR 在束内率）: 0.0
- candidate_space_failure_rate（候选空间失败率）: 1.0
- ranking_failure_rate（排序失败率）: 0.0
- upstream_boundary_failure_rate（上游边界失败率）: 1.0
- synthesis_failure_rate（合成失败率）: 0.0
- first_wrong_layer_distribution（首个错误层分布）: {'language_target': 42, 'semantic_domain': 83, 'task_scope': 58}
- rejected_by_layer_distribution（拒绝层分布）: {'support_gate': 93, 'language_target': 32, 'task_scope': 42, 'semantic_domain': 33}

## Clone and Backtracking（克隆与回溯）
- clone_promotion_count（克隆提升数）: 0
- clone_discard_count（克隆丢弃数）: 2
- backtracking_event_count（回溯事件数）: 2

## Non-Claims（非主张）
- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a Wide-Beam Backtracking Search（宽束回溯搜索） diagnostic and training scaffold.
