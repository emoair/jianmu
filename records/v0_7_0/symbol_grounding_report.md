# v0.7.0 Symbol Grounding Curriculum（符号接地课程） Report

This is a Symbol Grounding（符号接地） scaffold, not a convergence claim.

## Config（配置）

- mode: medium
- population_per_layer（每层种群数量）: 32
- generations（训练代数）: 20
- top_k: 5
- train/eval/ood: 2200 / 600 / 200
- runtime seconds: 19.7954

## Before vs After（训练前后）

- before zh_number_expression_false_reject_rate（中文数字表达误拒率）: 1.0
- after zh_number_expression_false_reject_rate（中文数字表达误拒率）: 1.0
- before zh_number_targetir_exact_match（中文数字表达 TargetIR 精确匹配）: 0.0
- after zh_number_targetir_exact_match（中文数字表达 TargetIR 精确匹配）: 0.0
- before symbol_slot_accuracy（符号槽位准确率）: 0.0525
- after symbol_slot_accuracy（符号槽位准确率）: 0.0
- numeral_slot_accuracy（数字槽位准确率）: 0.0
- operator_slot_accuracy（运算符槽位准确率）: 0.0
- paired_arabic_zh_agreement（阿拉伯数字/中文数字成对一致率）: 0.0
- paired_group_targetir_consistency（成对组 TargetIR 一致率）: 0.0
- eval target_ir_exact_match（目标中间表示精确匹配）: 0.0
- ood_rejection_rate（分布外拒绝率）: 1.0
- ood_false_accept_rate（分布外误接收率）: 0.0

## Training Curve（训练曲线）

- g0:numeral_grounding=0.0, g1:numeral_grounding=0.0, g2:numeral_grounding=0.0, g3:numeral_grounding=0.0, g4:numeral_grounding=0.0, g5:operator_grounding=0.0, g6:operator_grounding=0.0, g7:operator_grounding=0.0, g8:operator_grounding=0.0, g9:operator_grounding=0.0, g10:structure_grounding=0.0, g11:structure_grounding=0.0, g12:structure_grounding=0.0, g13:structure_grounding=0.0, g14:structure_grounding=0.0, g15:mixed_replay=0.0, g16:mixed_replay=0.0, g17:mixed_replay=0.0, g18:mixed_replay=0.0, g19:mixed_replay=0.0

## Examples（样例）

- 三加四
- 十一减五
- 负三乘四
- 十二除以三
- 三加四乘五

## Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a symbol grounding curriculum scaffold.
