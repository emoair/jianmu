# RootFork Global Assimilation（根叉全局吸收） Report（报告）

## Global Beam Before / After（全局束前后）
- global_correct_targetir_in_beam_rate_before（吸收前正确目标中间表示在束内率）: 0.2733
- global_correct_targetir_in_beam_rate_after（吸收后正确目标中间表示在束内率）: 0.1
- candidate_space_failure_rate_before（吸收前候选空间失败率）: 0.7267
- candidate_space_failure_rate_after（吸收后候选空间失败率）: 0.9

## Assimilation（全局吸收）
- assimilation_record_count（吸收记录数）: 800
- updated_layer_distribution（更新层分布）: {'arithmetic_family': 1808, 'structure_policy': 4451, 'slot_binding_policy': 5412, 'target_builder': 7610}
- updated_option_distribution（更新选项分布）: {'arithmetic_family=literal_only': 1292, 'structure_policy=literal_value': 3876, 'slot_binding_policy=signed_number_order': 1809, 'target_builder=canonical_arithmetic_targetir': 7610, 'slot_binding_policy=surface_number_order': 3540, 'slot_binding_policy=chinese_number_order': 63, 'arithmetic_family=multiplication': 132, 'structure_policy=binary_operation': 575, 'arithmetic_family=exact_division': 135, 'arithmetic_family=subtraction': 168, 'arithmetic_family=addition': 81}

## Slot Binding Repair（槽位绑定修复）
- slot_binding_correct_rank_before / after（槽位正确排名前后）: 2.8175 / 2.5
- slot_binding_correct_score_before / after（槽位正确分数前后）: 5.4938 / 75.495
- first_low_score_correct_layer_distribution_before / after（首个正确低分层分布前后）: {'slot_binding_policy': 147} / {}

## Root Lifecycle（根生命周期）
- active_root_count（活跃根数）: 0
- starving_root_count（饥饿根数）: 73
- necrotic_archived_count（坏死归档根数）: 204
- replacement_root_count（替代根数）: 0

## OOD Metric Reconciliation（分布外指标口径统一）
- ood_false_accept_before / after（分布外误接收前后）: 0.6667 / 0.6667
- ood_metric_consistency_passed（分布外指标一致性通过）: True
- arithmetic_supported_retention_rate（算术支持保留率）: 1.0

## Real Scale Ladder（真实规模阶梯）
- scale_ladder_results（规模阶梯结果）: [{'scale_label': 'small', 'beam_size': 24, 'subbeam_size': 24, 'generations': 4, 'train_limit': 300, 'eval_limit': 150, 'ood_limit': 100, 'run_id': 'small:7db936fe16', 'started_at': 1779284195.0015, 'ended_at': 1779284210.7797, 'runtime_seconds': 15.7782, 'skipped': False, 'evaluator_name': 'free_global_beam', 'guard_state': 'ood_guard_applied', 'population_state': 'assimilated', 'global_correct_targetir_in_beam_rate': 0.0333, 'candidate_space_failure_rate': 0.9667, 'seeded_free_subbeam_correct_targetir_rate': 0.0, 'subbeam_rescue_rate': 0.0, 'ood_false_accept_rate': 0.66, 'ood_sample_count': 100}, {'scale_label': 'medium', 'beam_size': 48, 'subbeam_size': 48, 'generations': 8, 'train_limit': 800, 'eval_limit': 300, 'ood_limit': 150, 'run_id': 'medium:c0322ed84f', 'started_at': 1779284210.7797, 'ended_at': 1779284269.8173, 'runtime_seconds': 59.0376, 'skipped': False, 'evaluator_name': 'free_global_beam', 'guard_state': 'ood_guard_applied', 'population_state': 'assimilated', 'global_correct_targetir_in_beam_rate': 0.0367, 'candidate_space_failure_rate': 0.9633, 'seeded_free_subbeam_correct_targetir_rate': 0.0, 'subbeam_rescue_rate': 0.0, 'ood_false_accept_rate': 0.6667, 'ood_sample_count': 150}, {'scale_label': 'large', 'beam_size': 96, 'subbeam_size': 96, 'generations': 12, 'train_limit': 1200, 'eval_limit': 500, 'ood_limit': 200, 'run_id': 'large:615914d08b', 'skipped': True, 'skip_reason': 'bounded_runtime_skip', 'runtime_seconds': 0.0}]
- scale_limited_likely（可能受规模限制）: True
- structural_failure_likely（可能结构性失败）: False
- assimilation_effect_likely（可能存在吸收效果）: False

## Non-Claims（非主张）
- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This is a RootFork Global Assimilation（根叉全局吸收） scaffold.
