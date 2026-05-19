# Paraphrase-Invariant TargetIR Training（复述不变目标中间表示训练）

v0.6.5 is a development scaffold for group-level training over Paraphrase Group（复述组） labels. It remains inside the BranchChain（分支链） → AtomicSynthesis（原子结构合成） → TargetIR（目标中间表示） → CEmitter（C 代码发射器） → Compiler Sandbox（编译器沙箱） → DarwinForge（达尔文进化炉） direction.

## 1. Why Paraphrase Invariance（为什么需要复述不变性）

v0.6.4 built an Architecture-Aligned Dataset（架构对齐数据集）, but it only showed that labels are more aligned with JianMu's architecture. The next step is to evaluate whether BranchChain（分支链） and AtomicSynthesis（原子结构合成） can move multiple surface forms toward the same TargetIR（目标中间表示）.

The desired training shape is:

multiple Chinese / math paraphrases → same Canonical TargetIR（规范目标中间表示）

This is more important than single input_text accuracy alone.

## 2. Paraphrase Group（复述组）

A Paraphrase Group（复述组） contains samples with:

- different input_text
- different input_mode
- the same target_ir_canonical
- the same expected_output
- possibly different early BranchDecision（分支决策） values such as explicit_C（显式 C）, implicit_C（隐式 C）, and math_expression_context（数学表达上下文）
- the same final TargetIR（目标中间表示） objective

## 3. Invariance vs Correctness（一致性与正确性）

Group Consistency（组内一致性） is not sufficient by itself.

Bad collapse example:

all inputs → `add(lit(1),lit(2))`

This is consistent, but it is wrong for the `mul_2_3` group. Therefore group fitness must keep TargetIR exact match（目标中间表示精确匹配） above consistency.

The reported metrics include:

- target_ir_exact_match（目标中间表示精确匹配）
- group_consistency（组内一致性）
- cross_mode_consistency（跨输入模式一致性）
- OOD rejection correctness（分布外拒绝正确性）
- paraphrase_collapse_rate（复述坍缩率）

## 4. Cross-Mode Consistency（跨输入模式一致性）

Within the same group, zh_technical_mixed（中文技术混合）, zh_natural（中文自然语言）, and math_expression（纯数学表达） should converge to the same TargetIR（目标中间表示）.

Example group:

- `写一个 C 程序输出 1+2`
- `输出 1+2`
- `计算一加二`
- `1+2`

Expected TargetIR（目标中间表示）:

`add(lit(1),lit(2))`

## 5. OOD Behavior（分布外行为）

ood_english（英语分布外） and ood_unrelated（无关分布外） samples do not participate in positive paraphrase training. They should be rejected by no_confident_branch_reject（无可信分支拒绝） or typed_rejection（类型化拒绝） without using an oracle-assisted parser（预言机辅助解析器）.

## 6. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a paraphrase-invariance training scaffold.
