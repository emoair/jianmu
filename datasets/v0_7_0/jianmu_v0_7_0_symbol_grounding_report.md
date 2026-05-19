# v0.7.0 Symbol Grounding Curriculum（符号接地课程） Dataset Report

This dataset provides teacher labels for Symbol Grounding（符号接地） while candidate generation only sees Raw Symbol Feature（原始符号特征） values.

## Summary（摘要）

- total: 3000
- split counts: {'train': 2200, 'eval': 600, 'ood': 200}
- curriculum_stage counts: {'numeral_grounding': 646, 'operator_grounding': 1076, 'structure_grounding': 1078, 'ood': 200}
- input_mode counts: {'arabic_math_expression': 701, 'zh_number_expression': 701, 'paired_zh_natural': 699, 'mixed_zh_arabic': 699, 'ood_english': 67, 'ood_unrelated': 67, 'unsupported_arithmetic': 66}
- paired_group count（成对复述组数量）: 634

## Examples（样例）

- arabic_math_expression: -6 -> lit(-6)
- zh_number_expression: 负六 -> lit(-6)
- paired_zh_natural: 计算负六 -> lit(-6)
- mixed_zh_arabic: 输出负六 -> lit(-6)
- ood_english: calculate 16 plus 17 -> None
- ood_unrelated: 写一首关于数字15的诗 -> None
- unsupported_arithmetic: 输出 5/4 -> None

## Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a Symbol Grounding Curriculum（符号接地课程） scaffold.
