# v0.6.4 Architecture-Aligned Dataset（架构对齐数据集） Report

This is a dataset realignment experiment for BranchChain（分支链） and TargetIR（目标中间表示） regeneration.

## Dataset Summary（数据集摘要）

- dataset size（数据集规模）: 40
- input_mode counts（输入模式计数）: {'zh_technical_mixed': 8, 'zh_natural': 16, 'math_expression': 8, 'ood_english': 4, 'ood_unrelated': 4}
- paraphrase_group counts（复述组计数）: {'add_1_2': 4, 'mul_2_3': 4, 'div_8_2': 4, 'add_mul_1_2_3': 4, 'paren_add_mul_1_2_3': 4, 'sub_10_3': 4, 'reduce_add_2_3_4': 4, 'add_neg1_2': 4, 'unsupported_language': 4, 'unsupported_non_programming': 2, 'unsupported_dangerous': 1, 'comparison_future': 1}
- supported count（支持样本数）: 32
- OOD count（分布外样本数）: 8
- language_target distribution（目标语言分布）: {'explicit_C': 8, 'implicit_C': 16, 'math_expression_context': 8, 'reject_unsupported_language': 4, '<none>': 4}

## Old vs New Dataset Comparison（旧/新数据集对比）

- old toy target_ir_exact_match（旧目标中间表示精确匹配）: 0.5
- new architecture-aligned target_ir_exact_match（新架构对齐目标中间表示精确匹配）: 0.5
- old false_reject_supported_count（旧误拒支持数）: 0
- new false_reject_supported_count（新误拒支持数）: 1
- old language_target reject count（旧目标语言层拒绝数）: 0
- new language_target reject count（新目标语言层拒绝数）: 0

## Rejection and Missing-Layer Metrics（拒绝与缺层指标）

- no_confidence_reject_count（无置信拒绝数）: 4
- correct_no_confidence_reject_count（正确无置信拒绝数）: 3
- wrong_no_confidence_reject_count（错误无置信拒绝数）: 1
- false_accept_unsupported_count（误接收不支持数）: 0
- false_reject_supported_count（误拒支持数）: 1
- true_missing_layer_rate（真正缺层率）: 0.0
- early_reject_short_path_rate（早停短路径率）: 0.125
- final target_ir_exact_match（最终目标中间表示精确匹配）: 0.5
- best target_ir_exact_match（最佳目标中间表示精确匹配）: 0.5

## OOD Evaluation（分布外评测）

- OOD english rejection behavior（英语分布外拒绝行为）: {'ood_english_count': 4, 'rejected_count': 4, 'accepted_count': 0, 'behavior': 'rejected'}

## Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a dataset realignment experiment.
