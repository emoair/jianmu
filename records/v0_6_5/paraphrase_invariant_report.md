# v0.6.5 Paraphrase-Invariant TargetIR Training（复述不变目标中间表示训练） Report

This is a group-level DarwinForge（达尔文进化炉） scaffold for BranchChain（分支链）, AtomicSynthesis（原子结构合成）, and TargetIR（目标中间表示） convergence.

## Dataset（数据集）

- dataset size（数据集规模）: 40
- supported paraphrase group count（支持复述组数量）: 8
- OOD count（分布外数量）: 8
- input_mode counts（输入模式计数）: {'math_expression': 8, 'ood_english': 4, 'ood_unrelated': 4, 'zh_natural': 16, 'zh_technical_mixed': 8}

## Sample-Level Metrics（单样本指标）

- generation 0 sample_target_ir_exact_match（第 0 代单样本目标中间表示精确匹配）: 0.5
- final sample_target_ir_exact_match（最终单样本目标中间表示精确匹配）: 0.5
- best sample_target_ir_exact_match（最佳单样本目标中间表示精确匹配）: 0.5

## Group-Level Metrics（组级指标）

- generation 0 group_targetir_consistency（第 0 代组内一致性）: 0.875
- final group_targetir_consistency（最终组内一致性）: 0.875
- best group_targetir_consistency（最佳组内一致性）: 0.875
- generation 0 group_targetir_exact_match（第 0 代组内目标中间表示正确率）: 0.5
- final group_targetir_exact_match（最终组内目标中间表示正确率）: 0.5
- best group_targetir_exact_match（最佳组内目标中间表示正确率）: 0.5
- cross_mode_consistency（跨输入模式一致性）: 0.875
- paraphrase_collapse_rate（复述坍缩率）: 0.125
- supported_all_rejected_group_count（支持组全拒绝数量）: 0
- group_inconsistent_count（组内不一致数量）: 1

## OOD Evaluation（分布外评测）

- ood_rejection_rate（分布外拒绝率）: 1.0
- ood_false_accept_rate（分布外误接收率）: 0.0

## Representative Group Predictions（代表性复述组预测）

- add_1_2: target=add(lit(1),lit(2)), predicted=['add(lit(1),lit(2))', 'add(lit(1),lit(2))', 'add(lit(1),lit(2))', 'add(lit(1),lit(2))'], exact=True, consistent=True
- add_mul_1_2_3: target=add(lit(1),mul(lit(2),lit(3))), predicted=['add(lit(1),lit(2))', 'add(lit(1),lit(2))', 'add(lit(1),lit(2))', 'add(lit(1),lit(2))'], exact=False, consistent=True
- add_neg1_2: target=add(lit(-1),lit(2)), predicted=['sub(lit(-1),lit(2))', 'sub(lit(-1),lit(2))', 'add(lit(-1),lit(2))', 'sub(lit(-1),lit(2))'], exact=False, consistent=False
- div_8_2: target=div(lit(8),lit(2)), predicted=['div(lit(8),lit(2))', 'div(lit(8),lit(2))', 'div(lit(8),lit(2))', 'div(lit(8),lit(2))'], exact=True, consistent=True
- mul_2_3: target=mul(lit(2),lit(3)), predicted=['mul(lit(2),lit(3))', 'mul(lit(2),lit(3))', 'mul(lit(2),lit(3))', 'mul(lit(2),lit(3))'], exact=True, consistent=True
- paren_add_mul_1_2_3: target=mul(add(lit(1),lit(2)),lit(3)), predicted=['mul(add(lit(1),lit(2)),lit(3))', 'mul(add(lit(1),lit(2)),lit(3))', 'mul(add(lit(1),lit(2)),lit(3))'], exact=False, consistent=True

## Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a Paraphrase-Invariant TargetIR Training（复述不变目标中间表示训练） scaffold.
