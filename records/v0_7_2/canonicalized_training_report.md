# Canonicalized Training Probe（规范化输入训练探针） Report

## Config（配置）
- mode: medium
- population_per_layer（每层种群数量）: 32
- generations（训练代数）: 10
- top_k（候选保留数量）: 5
- train/eval/ood: 1200 / 400 / 200

## Raw Input Training（原始输入训练） vs Canonical Input Training（规范输入训练）
- raw final target_ir_exact_match（原始输入 TargetIR 精确匹配）: 0.0
- canonical final target_ir_exact_match（规范输入 TargetIR 精确匹配）: 0.0
- raw zh_number_expression_false_reject_rate（原始中文数字误拒率）: 1.0
- canonical zh_number_expression_false_reject_rate（规范中文数字误拒率）: 0.02
- raw zh_number_targetir_exact_match（原始中文数字 TargetIR 精确匹配）: 0.0
- canonical zh_number_targetir_exact_match（规范中文数字 TargetIR 精确匹配）: 0.0
- raw ood_false_accept_rate（原始分布外误接收率）: 0.0
- canonical ood_false_accept_rate（规范分布外误接收率）: 0.045
- OOD Evaluation（分布外评测） raw/canonical false accept: 0.0 / 0.045
- raw_vs_canonical_delta（原始与规范差值）: {'target_ir_exact_match': 0.0, 'zh_number_expression_false_reject_rate': -0.98, 'zh_number_targetir_exact_match': 0.0, 'ood_false_accept_rate': 0.045}

## Stratified Evaluation（分层评测）
- negative_number_targetir_exact_match（负数 TargetIR 精确匹配）: 0.0
- parentheses_targetir_exact_match（括号 TargetIR 精确匹配）: 0.0
- mixed_precedence_targetir_exact_match（混合优先级 TargetIR 精确匹配）: 0.0
- exact_division_targetir_exact_match（精确除法 TargetIR 精确匹配）: 0.0
- unsupported_arithmetic_false_accept_rate（不支持算术误接收率）: 0.0

## Examples（示例）
| raw_text（原始文本） | canonical_text（规范文本） | raw_pred | canonical_pred | target_ir_true | raw_exact | canonical_exact |
|---|---|---|---|---|---|---|

## Non-Claims（非主张）
- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a Canonicalized Training Probe（规范化输入训练探针）, not a release claim.
