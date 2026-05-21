# Boundary-Aware Dataset Curriculum（边界感知数据课程）

## Dataset Scale Summary（数据规模摘要）
- scale（规模）: medium
- total（总数）: 30000

## Boundary Label Distribution（边界标签分布）
- {'future_domain_candidate': 4500, 'true_false_accept_trap': 4500, 'current_supported': 13500, 'hard_ood': 4500, 'near_ood_generalization_candidate': 2400, 'label_review_candidate': 600}

## Nutrient / Toxic Policy（养分 / 毒性策略）
- {'weak_positive_on_current_reject': 4500, 'positive_on_correct_reject': 9000, 'positive_on_correct_accept': 13500, 'neutral_on_current_reject': 2400, 'no_training_signal_review_only': 600}

## Split and Leakage Audit（切分与泄漏审计）
- audit_passed（审计通过）: True
- duplicate_input_count（重复输入数）: 0
- train_eval_input_leakage_count（训练评测输入泄漏数）: 0

## Curriculum Schedule（课程调度）
- curriculum_stage_count（课程阶段数）: 6

## Non-Claims（非主张）
- This dataset does not prove stable convergence, solved arithmetic, general program synthesis, or solved OOD.
