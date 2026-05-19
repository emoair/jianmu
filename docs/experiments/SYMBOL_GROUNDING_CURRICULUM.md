# v0.7.0 Symbol Grounding Curriculum

This document defines the v0.7.0 Symbol Grounding Curriculum（符号接地课程） experiment.

## 1. Why v0.7.0（为什么升到 v0.7.0）

v0.6.x built the BranchChain scaffold（分支链骨架）, Confidence-Gated Continuation（置信度守卫式继续）, Architecture-Aligned Dataset（架构对齐数据集）, Paraphrase Group（复述组） evaluation, Hindsight Branch Re-Ranking（回看式重排）, Perfect-Layer Backtracking（完美层回溯）, and Large Dataset Full Training Probe（大数据集全量训练探针）.

v0.7.0 starts a new capability line: Symbol Grounding（符号接地）. The goal is to study whether Chinese symbols, Chinese numerals, and operator words can be connected to TargetIR（目标中间表示） slots and structures through paired examples and fitness feedback, rather than through a handwritten parser.

## 2. Not a handwritten parser（不是手写解析器）

The inference path must not hardcode:

- 三 = 3
- 十一 = 11
- 加 = +
- 减 = -
- 乘 = *
- 除以 = /

The dataset generator may know the correct TargetIR（目标中间表示） because supervised training needs teacher labels. Surface features may expose Raw Symbol Feature（原始符号特征） values such as the raw character “三” or raw word “加”, but they must not expose normalized_number=3 or parsed_operator=add.

## 3. Teacher label vs inference feature（教师标签与推理特征）

The dataset generator provides teacher labels（教师标签）:

- target_ir_canonical
- expected_output
- symbol_slots
- operator_slots

Candidate generation（候选生成） and BranchChain（分支链） inference must not read those labels as features. They are only used after prediction for evaluation and reward.

## 4. Curriculum stages（课程阶段）

Stage A: Numeral Grounding（数字接地）

- 三, 四, 十一, 二十, 负三
- lit(3), lit(4), lit(11), lit(20), lit(-3)

Stage B: Operator Grounding（运算符接地）

- 三加四
- 三减四
- 三乘四
- 十二除以三

Stage C: Structure Grounding（结构接地）

- 三加四乘五
- 三乘四加五
- 括号里三加四再乘五
- 负三加四
- 十二除以三加五

## 5. Metrics（指标）

- zh_number_expression_false_reject_rate（中文数字表达误拒率）
- symbol_slot_accuracy（符号槽位准确率）
- numeral_slot_accuracy（数字槽位准确率）
- operator_slot_accuracy（运算符槽位准确率）
- zh_number_task_scope_continue_rate（中文数字表达任务范围继续率）
- zh_number_targetir_exact_match（中文数字表达 TargetIR 精确匹配）
- paired_arabic_zh_agreement（阿拉伯数字/中文数字成对一致率）

## 6. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a Symbol Grounding Curriculum（符号接地课程） scaffold.

