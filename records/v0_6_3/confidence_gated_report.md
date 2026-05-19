# v0.6.3 Confidence-Gated Guarded BranchChain（置信度守卫式带守卫分支链） Report

support_gate（支持/拒绝门） remains for compatibility but is downgraded to an ordinary BranchChain（分支链） layer.

## No-Confidence Rejection（无置信拒绝） Summary

- no_confidence_reject_count（无置信拒绝数）: 11
- correct_no_confidence_reject_count（正确无置信拒绝数）: 2
- wrong_no_confidence_reject_count（错误无置信拒绝数）: 9
- typed_reject_count（类型化拒绝数）: 3
- false_accept_unsupported_count（误接收不支持数）: 0
- false_reject_supported_count（误拒支持数）: 9
- rejected_by_layer_distribution（拒绝层分布）: {'language_target': 11, 'task_scope': 3}
- continue_threshold by layer（分层继续阈值）: {'task_scope': 20, 'language_target': 15, 'semantic_domain': 15, 'support_gate': 15, 'arithmetic_family': 15, 'structure_policy': 10, 'slot_binding_policy': 10, 'target_builder': 10}

## Final vs Best（最终与历史最佳）

- generation 0 target_ir_exact_match（目标中间表示精确匹配）: 0.25
- final target_ir_exact_match（最终目标中间表示精确匹配）: 0.25
- best target_ir_exact_match（历史最佳目标中间表示精确匹配）: 0.25
- final missing_layer_rate（最终缺层率）: 0.6

## Per-Layer Gate Metrics（分层守卫指标）

- per_layer_reject_count（分层拒绝数）: {'language_target': 11, 'task_scope': 3}
- per_layer_continue_rate（分层继续率）: {'task_scope': 0.85, 'language_target': 0.3529, 'semantic_domain': 1.0, 'support_gate': 1.0, 'arithmetic_family': 1.0, 'structure_policy': 1.0, 'slot_binding_policy': 1.0, 'target_builder': 1.0}
- confidence_margin_by_layer（分层置信度间隔）: {'task_scope': 14.4, 'language_target': 2.0588, 'semantic_domain': 20.6667, 'support_gate': 12.0, 'arithmetic_family': 13.3333, 'structure_policy': 19.5, 'slot_binding_policy': 20.0, 'target_builder': 15.8333}

## Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
