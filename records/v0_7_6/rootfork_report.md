# RootFork Sub-Beam Regrowth（根叉子束再生） Report（报告）

## Path Forcing Summary（强制路径摘要）
- path_forcing_exact_match_rate（强制路径精确匹配率）: 1.0

## Router Score Diagnostics（路由分数诊断）
- correct_option_rank_by_layer（正确选项逐层排名）: {'arithmetic_family': 1.145, 'language_target': 1.4975, 'semantic_domain': 1.0, 'slot_binding_policy': 2.8175, 'structure_policy': 1.1925, 'support_gate': 1.0, 'target_builder': 1.0, 'task_scope': 1.0}
- first_low_score_correct_layer_distribution（首个正确选项低分层分布）: {'slot_binding_policy': 147}
- first_pruned_correct_layer_distribution（首个正确选项被剪层分布）: {}
- fork_layer_distribution（分叉层分布）: {'arithmetic_family': 653, 'slot_binding_policy': 147}

## Path-Prior Seeding（路径先验播种）
- path_prior_seed_count（路径先验种子数）: 23
- branch_neuron_updated_count（分支神经元更新数）: 169

## Global Beam（全局束）
- correct_targetir_in_beam_rate（正确目标中间表示在束内率）: 0.1
- candidate_space_failure_rate（候选空间失败率）: 0.9

## Sub-Beam Regrowth（子束再生）
- teacher_subbeam_correct_targetir_rate（教师子束正确目标中间表示率）: 1.0
- seeded_free_subbeam_correct_targetir_rate（播种自由子束正确目标中间表示率）: 1.0
- subbeam_rescue_rate（子束救援率）: 0.375
- rescued_sample_count（被救援样本数）: 300

## OOD Guard Balancing（分布外守卫平衡）
- ood_false_accept_before（分布外误接收前）: 0.0
- ood_false_accept_after（分布外误接收后）: 0.0
- arithmetic_supported_retention_rate（算术支持保留率）: 1.0

## Scale Ladder（规模阶梯）
- scale_ladder_results（规模阶梯结果）: [{'scale': 'small', 'beam_size': 24, 'subbeam_size': 24, 'generations': 4, 'train_limit': 300, 'eval_limit': 150, 'ood_limit': 100, 'skipped': False, 'correct_targetir_in_beam_rate': 0.1, 'correct_targetir_in_subbeam_rate': 1.0, 'subbeam_rescue_rate': 0.375, 'candidate_space_failure_rate': 0.9, 'ood_false_accept_rate': 0.6667, 'runtime_seconds': 156.4265}, {'scale': 'medium', 'beam_size': 48, 'subbeam_size': 48, 'generations': 8, 'train_limit': 800, 'eval_limit': 300, 'ood_limit': 150, 'skipped': False, 'correct_targetir_in_beam_rate': 0.1, 'correct_targetir_in_subbeam_rate': 1.0, 'subbeam_rescue_rate': 0.375, 'candidate_space_failure_rate': 0.9, 'ood_false_accept_rate': 0.6667, 'runtime_seconds': 156.4265}, {'scale': 'large', 'beam_size': 96, 'subbeam_size': 96, 'generations': 12, 'train_limit': 1200, 'eval_limit': 500, 'ood_limit': 200, 'skipped': True, 'skip_reason': 'not_run_in_bounded_probe'}]
- scale_limited_likely（可能受规模限制）: False
- structural_failure_likely（可能结构性失败）: False

## Non-Claims（非主张）
- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This is a RootFork Sub-Beam Regrowth（根叉子束再生） scaffold.
