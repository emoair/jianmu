# Boundary-Aware Dataset Curriculum（边界感知数据课程）

## Dataset Scale Summary（数据规模摘要）
- scales_completed（完成规模）: ['medium', 'large']
- dataset_total_size_by_scale（各规模总数）: {'medium': 30000, 'large': 100000}

## Boundary Label Distribution（边界标签分布）
- current_supported（当前支持）: 45000
- hard_ood（硬分布外）: 15000
- true_false_accept_trap（真正误接收陷阱）: 15000
- future_domain_candidate（未来能力候选）: 15000
- near_ood_generalization_candidate（近邻泛化候选）: 8000

## Nutrient / Toxic Policy（养分 / 毒性策略）
- nutrient_policy_distribution（养分策略分布）: {'positive_on_correct_accept': 45000, 'positive_on_correct_reject': 30000, 'weak_positive_on_current_reject': 15000, 'neutral_on_current_reject': 8000, 'no_training_signal_review_only': 2000}

## Split and Leakage Audit（切分与泄漏审计）
- audit_passed（审计通过）: True
- duplicate_input_count（重复输入数）: 0
- train_eval_input_leakage_count（训练评测泄漏数）: 0
- non_supported_has_targetir_count（非支持样本含目标中间表示数）: 0

## Curriculum Schedule（课程调度）
- curriculum_stage_count（课程阶段数）: 6

## Candidate Source Usage（候选来源使用）
- {'used_v0_8_4_candidates': True, 'source_candidate_count': 193}

## Probe Result（探针结果）
- {'dataset_load_success': True, 'audit_passed': True, 'curriculum_stage_count': 6, 'current_supported_count': 45000, 'hard_ood_count': 15000, 'true_false_accept_trap_count': 15000, 'future_domain_candidate_count': 15000, 'near_ood_candidate_count': 8000, 'boundary_reward_policy_valid': True, 'non_supported_targetir_leak_count': 0, 'future_domain_train_current_leak_count': 0, 'near_ood_train_current_leak_count': 0, 'sample_pipeline_success_rate': 1.0}

## Updated Mainline Judgment（更新主线判断）
- This version rebuilds the dataset ecology; it does not change BranchChain or RootForge main logic.

## Non-Claims（非主张）
- This does not prove stable convergence.
- This does not prove solved arithmetic, solved OOD, or a fully emergent rejection gate.
