# v0.6.7 Perfect-Layer Backtracking Curriculum（完美层回溯课程训练） Report

This is a toy/synthetic BranchChain（分支链） curriculum scaffold. The 100% perfect layer rule is only for toy/synthetic deterministic data（玩具/合成确定性数据）.

## Summary（摘要）

- dataset size（数据集规模）: 40
- generations（代数）: 120
- layer order（层顺序）: ['task_scope', 'language_target', 'semantic_domain', 'support_gate', 'arithmetic_family', 'structure_policy', 'slot_binding_policy', 'target_builder']
- perfect_layer_count（完美冻结层数）: 0
- active_layer_final（最终当前训练层）: task_scope
- trainable_layers_final（最终可训练层）: []
- blocked_layers（阻塞层）: ['task_scope']

## Perfect Freeze Events（完美冻结事件）

- none

## Backtracking Events（回溯事件）

- generation 8: active=task_scope, unfrozen=['task_scope'], outcome=no_improvement
- generation 14: active=task_scope, unfrozen=['task_scope'], outcome=no_improvement
- generation 20: active=task_scope, unfrozen=['task_scope'], outcome=blocked

## Metrics（指标）

- per_layer_exact_accuracy（分层精确准确率）: {'task_scope': 0.9, 'language_target': 0.8611, 'semantic_domain': 0.9688, 'arithmetic_family': 0.75, 'structure_policy': 0.7188, 'slot_binding_policy': 0.8438, 'target_builder': 0.9688}
- per_layer_correct_count（分层正确数）: {'task_scope': 36, 'language_target': 31, 'semantic_domain': 31, 'arithmetic_family': 24, 'structure_policy': 23, 'slot_binding_policy': 27, 'target_builder': 31}
- per_layer_required_count（分层要求数）: {'task_scope': 40, 'language_target': 36, 'semantic_domain': 32, 'arithmetic_family': 32, 'structure_policy': 32, 'slot_binding_policy': 32, 'target_builder': 32}
- target_ir_exact_match_final（最终目标中间表示精确匹配）: 0.5
- target_ir_exact_match_best（最佳目标中间表示精确匹配）: 0.5
- low_score_correct_count（低分正确候选数量）: 37
- high_score_wrong_count（高分错误候选数量）: 20

## Toy-Only Warning（玩具数据限定警告）

Perfect-Layer Curriculum（完美层课程） assumes deterministic toy labels. Larger or noisy data must use Highest-Stable Threshold Search（最高稳定阈值搜索） instead of hard 100%.

## Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a toy/synthetic curriculum dynamics scaffold.
