# v0.6.9 Large Dataset Full Training Probe（大数据集全量训练探针） Report

This is a probe（探针）, not a release claim or convergence claim.

## Parameter Config（参数配置）

- mode: medium
- population_per_layer（每层种群数量）: 32
- generations（训练代数）: 8
- top_k_candidates（候选保留数量）: 5
- train sample count: 1200
- eval sample count: 600
- runtime seconds: 159.5804
- runtime note（运行说明）: bounded runtime override; default mode parameters were not fully completed

## Before vs After（训练前后）

- before target_ir_exact_match（目标中间表示精确匹配）: 0.5481
- after target_ir_exact_match（目标中间表示精确匹配）: 0.5481
- after unsupported_rejection_rate（不支持拒绝率）: 0.75
- after false_accept_unsupported_rate（不支持误接收率）: 0.25

## Full-Split Evaluation（全切分评测）

- eval_ood: target_ir_exact_match=0.0, unsupported_rejection_rate=0.75, false_accept_unsupported_rate=0.25
- eval_seen_target_unseen_paraphrase: target_ir_exact_match=0.0, unsupported_rejection_rate=0.0, false_accept_unsupported_rate=0.0
- eval_unseen_target: target_ir_exact_match=0.59, unsupported_rejection_rate=0.0, false_accept_unsupported_rate=0.0

## Stratified Evaluation（分层评测） by Input-Mode Metrics（输入模式指标）

- comparison_future: target_ir_exact_match=0.0, false_reject_supported_rate=0.0, false_accept_unsupported_rate=0.0
- explicit_c: target_ir_exact_match=0.5882, false_reject_supported_rate=0.0, false_accept_unsupported_rate=0.0
- implicit_c: target_ir_exact_match=0.6061, false_reject_supported_rate=0.0, false_accept_unsupported_rate=0.0
- math_expression: target_ir_exact_match=0.6061, false_reject_supported_rate=0.0, false_accept_unsupported_rate=0.0
- ood_english: target_ir_exact_match=0.0, false_reject_supported_rate=0.0, false_accept_unsupported_rate=0.0
- ood_unrelated: target_ir_exact_match=0.0, false_reject_supported_rate=0.0, false_accept_unsupported_rate=0.0
- unsupported_arithmetic: target_ir_exact_match=0.0, false_reject_supported_rate=0.0, false_accept_unsupported_rate=1.0
- zh_natural: target_ir_exact_match=0.5455, false_reject_supported_rate=0.0, false_accept_unsupported_rate=0.0
- zh_number_expression: target_ir_exact_match=0.0, false_reject_supported_rate=1.0, false_accept_unsupported_rate=0.0
- zh_technical_mixed: target_ir_exact_match=0.597, false_reject_supported_rate=0.0, false_accept_unsupported_rate=0.0

## Expression-Family Metrics（表达式族指标）

- None: target_ir_exact_match=0.0, sample_count=200
- addition: target_ir_exact_match=0.0976, sample_count=123
- exact_division: target_ir_exact_match=0.3913, sample_count=46
- mixed_precedence: target_ir_exact_match=0.0, sample_count=43
- multiplication: target_ir_exact_match=0.5455, sample_count=55
- parentheses: target_ir_exact_match=0.3273, sample_count=55
- subtraction: target_ir_exact_match=0.5128, sample_count=78

## Known Diagnostic Targets（已知诊断目标）

- zh_number_expression false reject（中文数字表达误拒）: 200 / 1.0
- unsupported_arithmetic false accept（不支持算术误接收）: 50 / 1.0
- task_scope no-confident reject（任务范围层无可信拒绝）: 251
- arithmetic_family typed reject（算术族类型化拒绝）: 0
- structure_policy typed reject（结构策略类型化拒绝）: 0

## Training Curve（训练曲线）

- g0=0.6325, g1=0.6325, g2=0.6325, g3=0.6325, g4=0.6325, g5=0.6325, g6=0.6325, g7=0.6325

## Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a Large Dataset Full Training Probe（大数据集全量训练探针）, not a release claim.
