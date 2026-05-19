# Architecture-Aligned Dataset（架构对齐数据集）

v0.6.4 is a dataset realignment experiment for BranchChain（分支链）, Confidence-Gated Continuation（置信度守卫式继续）, AtomicSynthesis（原子结构合成）, and TargetIR（目标中间表示） regeneration. It is not a v0.5 release claim.

## 1. Why v0.6.3 Over-Rejected（为什么 v0.6.3 过度拒绝）

v0.6.3 showed too many false rejects at language_target（目标语言层）. The toy dataset treated implicit C（隐式 C） and pure math expressions（纯数学表达） as `unknown`, even when they were valid inputs for the current JianMu C-program experiment.

That label shape made the BranchChain（分支链） learn a contradictory path: `unknown` language should still continue into C TargetIR（目标中间表示） generation. This increased no_confident_branch_reject（无可信分支拒绝） at language_target（目标语言层）.

This is not a failure of confidence gate（置信度守卫） itself. It is a mismatch between dataset labels and JianMu's current architecture.

## 2. New Input Modes（新输入模式）

- zh_natural（中文自然语言）: Chinese task descriptions such as `输出 1+2`.
- math_expression（纯数学表达）: surface expressions such as `1+2*3`.
- zh_technical_mixed（中文技术混合）: Chinese inputs containing C / printf / main tokens.
- ood_english（分布外英语）: English natural-language inputs used as OOD Evaluation（分布外评测） negatives.
- ood_unrelated（分布外无关任务）: poetry, network, file, or unrelated requests.

## 3. New language_target Labels（新的目标语言标签）

The dataset avoids using `unknown` for supported samples.

- explicit_C（显式 C）: the input explicitly mentions C / printf / main.
- implicit_C（隐式 C）: Chinese asks to output / compute / print but does not explicitly name C.
- math_expression_context（数学表达上下文）: pure math expressions accepted by the current C regeneration experiment.
- reject_unsupported_language（拒绝不支持语言）: English natural-language inputs.

For example, `输出 8/2` is implicit_C（隐式 C） or math_expression_context（数学表达上下文）, not `unknown`.

## 4. Paraphrase Groups（复述组）

The training target is not one sentence to one hard label. The target is multiple surface forms mapping to the same Canonical TargetIR（规范目标中间表示）.

Example TargetIR（目标中间表示）:

`add(lit(1),mul(lit(2),lit(3)))`

Aligned surface forms:

- `写一个 C 程序输出 1+2*3`
- `输出 1+2*3`
- `打印一加二乘三`
- `1+2*3`

## 5. OOD Eval（分布外评测）

English natural-language code requests are not added as positive training examples. They are kept primarily as OOD Evaluation（分布外评测） cases:

- `calculate one plus two`
- `sum of 1 and 2`
- `write a C program to output 1+2`

The expected behavior is that BranchChain（分支链） lacks a confident continuation and returns no_confident_branch_reject（无可信分支拒绝） or a learned typed rejection, without invoking an oracle-assisted parser（预言机辅助解析器）.

## 6. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a dataset realignment experiment.
