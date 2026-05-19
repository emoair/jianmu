# v0.6.2 Highest-Stable Threshold Search（最高稳定阈值搜索） Report

This is a threshold-search scaffold for BranchChain（分支链） curriculum training.

## Final vs Best（最终与历史最佳）

- generation 0 mean_fitness（平均适应度）: 2.9067
- final mean_fitness（最终平均适应度）: 3.2817
- best mean_fitness（历史最佳平均适应度）: 3.3017
- generation 0 target_ir_exact_match（目标中间表示精确匹配）: 0.5
- final target_ir_exact_match（最终目标中间表示精确匹配）: 0.55
- best target_ir_exact_match（历史最佳目标中间表示精确匹配）: 0.55
- final missing_layer_rate（最终缺层率）: 0.0

## Threshold Events（阈值事件）

- freeze events（冻结事件）: [{'generation': 30, 'layer': 'task_scope', 'reason': 'freeze_criteria_met', 'frozen_threshold': 0.9}, {'generation': 44, 'layer': 'language_target', 'reason': 'freeze_criteria_met', 'frozen_threshold': 0.93}, {'generation': 45, 'layer': 'semantic_domain', 'reason': 'freeze_criteria_met', 'frozen_threshold': 0.95}]
- threshold anneal events（阈值退火事件）: [{'generation': 11, 'layer': 'task_scope', 'from': 0.98, 'to': 0.955}, {'generation': 17, 'layer': 'task_scope', 'from': 0.955, 'to': 0.93}, {'generation': 23, 'layer': 'task_scope', 'from': 0.93, 'to': 0.905}, {'generation': 29, 'layer': 'task_scope', 'from': 0.905, 'to': 0.9}, {'generation': 37, 'layer': 'language_target', 'from': 0.98, 'to': 0.955}, {'generation': 43, 'layer': 'language_target', 'from': 0.955, 'to': 0.93}, {'generation': 54, 'layer': 'support_gate', 'from': 0.95, 'to': 0.925}, {'generation': 60, 'layer': 'support_gate', 'from': 0.925, 'to': 0.9}]
- threshold block events（阈值阻塞事件）: []
- frozen_threshold_by_layer（各层冻结阈值）: {'task_scope': 0.9, 'language_target': 0.93, 'semantic_domain': 0.95}

## support_gate（支持/拒绝门）

- threshold history（阈值历史）: [{'threshold': 0.95, 'accuracy': 0.75, 'recall_at_k': 0.8, 'missing_rate': 0.1, 'correct_count': 15, 'total_count': 20}, {'threshold': 0.95, 'accuracy': 0.75, 'recall_at_k': 0.8, 'missing_rate': 0.1, 'correct_count': 15, 'total_count': 20}, {'threshold': 0.95, 'accuracy': 0.8, 'recall_at_k': 0.8, 'missing_rate': 0.05, 'correct_count': 16, 'total_count': 20}, {'threshold': 0.95, 'accuracy': 0.8, 'recall_at_k': 0.8, 'missing_rate': 0.05, 'correct_count': 16, 'total_count': 20}, {'threshold': 0.95, 'accuracy': 0.8, 'recall_at_k': 0.8, 'missing_rate': 0.05, 'correct_count': 16, 'total_count': 20}, {'threshold': 0.95, 'accuracy': 0.75, 'recall_at_k': 0.8, 'missing_rate': 0.05, 'correct_count': 15, 'total_count': 20}, {'threshold': 0.95, 'accuracy': 0.8, 'recall_at_k': 0.8, 'missing_rate': 0.05, 'correct_count': 16, 'total_count': 20}, {'threshold': 0.95, 'accuracy': 0.8, 'recall_at_k': 0.8, 'missing_rate': 0.05, 'correct_count': 16, 'total_count': 20}, {'threshold': 0.95, 'accuracy': 0.8, 'recall_at_k': 0.8, 'missing_rate': 0.05, 'correct_count': 16, 'total_count': 20}, {'threshold': 0.925, 'accuracy': 0.8, 'recall_at_k': 0.8, 'missing_rate': 0.05, 'correct_count': 16, 'total_count': 20}, {'threshold': 0.925, 'accuracy': 0.8, 'recall_at_k': 0.8, 'missing_rate': 0.05, 'correct_count': 16, 'total_count': 20}, {'threshold': 0.925, 'accuracy': 0.8, 'recall_at_k': 0.8, 'missing_rate': 0.05, 'correct_count': 16, 'total_count': 20}, {'threshold': 0.925, 'accuracy': 0.8, 'recall_at_k': 0.8, 'missing_rate': 0.05, 'correct_count': 16, 'total_count': 20}, {'threshold': 0.925, 'accuracy': 0.8, 'recall_at_k': 0.8, 'missing_rate': 0.05, 'correct_count': 16, 'total_count': 20}, {'threshold': 0.925, 'accuracy': 0.8, 'recall_at_k': 0.8, 'missing_rate': 0.05, 'correct_count': 16, 'total_count': 20}]
- winner accuracy（赢家准确率）: 0.8
- layer_recall@k（层级候选召回）: 0.8
- confusion matrix（混淆矩阵）: {'true_supported_pred_supported': 15, 'true_supported_pred_unsupported': 0, 'true_unsupported_pred_supported': 3, 'true_unsupported_pred_unsupported': 2}
- false reject supported（误拒支持样本）: 0
- false accept unsupported（误接收不支持样本）: 3

## Per-Layer Counts（分层整数正确数）

- arithmetic_family: actual_correct（实际正确数）=12, required_correct（要求正确数）=15, total（总数）=15
- language_target: actual_correct（实际正确数）=14, required_correct（要求正确数）=15, total（总数）=15
- semantic_domain: actual_correct（实际正确数）=15, required_correct（要求正确数）=15, total（总数）=15
- slot_binding_policy: actual_correct（实际正确数）=11, required_correct（要求正确数）=15, total（总数）=15
- structure_policy: actual_correct（实际正确数）=12, required_correct（要求正确数）=15, total（总数）=15
- support_gate: actual_correct（实际正确数）=16, required_correct（要求正确数）=19, total（总数）=20
- target_builder: actual_correct（实际正确数）=15, required_correct（要求正确数）=15, total（总数）=15
- task_scope: actual_correct（实际正确数）=19, required_correct（要求正确数）=20, total（总数）=20

## Selection Problem Notes（选择问题提示）

- arithmetic_family: layer_recall@k（层级候选召回）=0.8667 > winner_accuracy（赢家准确率）=0.8

## Curves（曲线）

- active_layer（当前训练层）: task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, task_scope, language_target, language_target, language_target, language_target, language_target, language_target, language_target, language_target, language_target, language_target, language_target, language_target, language_target, language_target, semantic_domain, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate
- target_ir_exact_match（目标中间表示精确匹配）: 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55
- mean_fitness（平均适应度）: 2.9067, 2.9067, 2.9067, 2.9067, 2.9067, 2.9067, 2.9067, 2.9067, 3.2467, 2.9067, 2.9067, 2.9067, 2.9067, 3.2467, 3.2467, 2.9067, 2.9067, 2.9067, 2.9067, 2.9067, 2.9067, 2.9067, 3.2467, 2.9067, 2.9067, 2.9067, 3.2467, 2.9067, 2.9067, 2.9067, 2.9067, 3.3017, 3.2867, 3.2867, 3.2867, 3.2867, 3.2867, 3.2867, 3.2867, 3.2867, 3.2867, 3.2867, 3.2867, 3.2867, 3.2867, 3.2867, 3.2867, 3.2867, 3.2817, 3.2817, 3.2817, 3.2817, 3.2817, 3.2817, 3.2817, 3.2817, 3.2817, 3.2817, 3.2817, 3.2817, 3.2817
- missing_layer_rate（缺层率）: 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.25, 0.2, 0.2, 0.2, 0.2, 0.25, 0.25, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.25, 0.2, 0.2, 0.2, 0.25, 0.2, 0.2, 0.2, 0.2, 0.05, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

## Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
