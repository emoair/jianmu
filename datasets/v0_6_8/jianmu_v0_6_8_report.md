# v0.6.8 Large Architecture-Aligned Dataset（大规模架构对齐数据集） Report

This deterministic local dataset supports Scale Smoke Benchmark（规模化冒烟基准） diagnostics for BranchChain（分支链）, Confidence-Gated Continuation（置信度守卫式继续）, AtomicSynthesis（原子结构合成）, and TargetIR（目标中间表示） regeneration.

## Summary（摘要）

- total samples: 6000
- split counts: {'train': 4200, 'eval_seen_target_unseen_paraphrase': 600, 'eval_unseen_target': 600, 'eval_ood': 600}
- supported / unsupported: 4800 / 1200
- paraphrase_group count（复述组数量）: 700
- average paraphrases per group（平均复述数）: 6.8571

## Distributions（分布）

- input_mode counts: {'explicit_c': 700, 'zh_technical_mixed': 1400, 'implicit_c': 700, 'zh_natural': 700, 'math_expression': 700, 'ood_english': 300, 'ood_unrelated': 300, 'unsupported_arithmetic': 300, 'comparison_future': 300, 'zh_number_expression': 600}
- expression_family counts: {'subtraction': 794, 'addition': 1421, 'exact_division': 501, 'parentheses': 692, 'mixed_precedence': 601, 'multiplication': 791}
- structure_policy counts: {'binary_operation': 2848, 'reduce_chain': 659, 'parenthesized_tree': 692, 'precedence_tree': 601}
- language_target distribution: {'explicit_C': 2100, 'implicit_C': 2000, 'math_expression_context': 1300, 'reject_unsupported_language': 300, 'None': 300}

## Dataset Leakage Check（数据泄漏检查）

- duplicate input count: 0
- train/eval_unseen_target group leakage: 0
- eval_seen_target_unseen_paraphrase input leakage: 0
- language_target=unknown count: 0
- OOD English supported count（英语分布外正样本数）: 0
- valid: True

## Examples（样例）

- explicit_c: 写一个 C 程序输出 2-48 -> sub(lit(2),lit(48))
- zh_technical_mixed: 写一个 C 程序，printf 输出 2-48 -> sub(lit(2),lit(48))
- implicit_c: 输出 2-48 -> sub(lit(2),lit(48))
- zh_natural: 计算 2 - 48 并输出 -> sub(lit(2),lit(48))
- math_expression: 2-48 -> sub(lit(2),lit(48))
- ood_english: calculate 26 plus 5 -> None
- ood_unrelated: 联网下载第 11 个文件 -> None
- unsupported_arithmetic: 输出 (((7+9))) + 6 的深层括号版本 -> None
- comparison_future: 请比较 13+5 和 3+17 哪个大 -> None
- zh_number_expression: 二减四十八等于多少 -> sub(lit(2),lit(48))

## Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a deterministic local dataset generation and Scale Smoke Benchmark（规模化冒烟基准） experiment.
