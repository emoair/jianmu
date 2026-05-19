# v0.6.8 Large Dataset + Scale Smoke Benchmark

This document defines the v0.6.8 Large Architecture-Aligned Dataset（大规模架构对齐数据集） and Scale Smoke Benchmark（规模化冒烟基准） experiment.

## 1. Why larger dataset（为什么需要更大数据集）

The 40-sample toy dataset is useful for checking BranchChain（分支链） shape, Confidence-Gated Continuation（置信度守卫式继续）, AtomicSynthesis（原子结构合成）, and TargetIR（目标中间表示） plumbing, but it is too small for curriculum dynamics.

With only a few boundary examples, Perfect-Layer Curriculum（完美层课程） can be blocked by one or two ambiguous samples. JianMu therefore needs more Chinese natural-language descriptions（中文自然语言描述）, Chinese technical mixed inputs（中文技术混合输入）, pure math expressions（纯数学表达）, Paraphrase Groups（复述组）, and OOD Evaluation（分布外评测） cases before later DarwinForge（达尔文进化炉） training experiments can be interpreted.

## 2. Why smoke benchmark in same version（为什么同版做冒烟基准）

Dataset generation alone is not enough. The new files must be consumed by the current BranchChain（分支链） and AtomicSynthesis（原子结构合成） path immediately, otherwise schema or label problems can hide until the next training version.

The Scale Smoke Benchmark（规模化冒烟基准） is only a sanity check（基本合理性检查）:

- it is not formal large training;
- it is not a performance release;
- it does not claim convergence;
- it records whether candidate generation, TargetIR（目标中间表示） comparison, and OOD Evaluation（分布外评测） can run on a larger deterministic dataset.

## 3. Dataset design（数据集设计）

The dataset covers:

- Chinese natural-language descriptions（中文自然语言描述）;
- Chinese technical mixed inputs（中文技术混合输入） with C / printf / main;
- pure math expressions（纯数学表达）;
- Chinese numeral expressions（中文数字表达）;
- explicit C（显式 C） and implicit C（隐式 C） contexts;
- negative numbers;
- addition, subtraction, multiplication, exact division;
- parentheses and precedence;
- chained addition;
- unsupported non-exact division and division by zero;
- English OOD Evaluation（英语分布外评测）;
- unrelated OOD tasks;
- comparison future unsupported samples.

The training target remains canonical TargetIR（规范目标中间表示）, not C source text.

## 4. Split design（切分设计）

The generated files are:

- train（训练集）;
- eval_seen_target_unseen_paraphrase（已见目标 / 未见复述评测）;
- eval_unseen_target（未见目标评测）;
- eval_ood（分布外评测）.

Train and eval_unseen_target（未见目标评测） do not share Paraphrase Group（复述组） identifiers. eval_seen_target_unseen_paraphrase（已见目标 / 未见复述评测） may share TargetIR（目标中间表示） with train, but it must use input_text values not present in train. eval_ood（分布外评测） is used for rejection behavior, not positive training.

## 5. No English positive training（不训练英语正样本）

English natural language is not a supported positive interface in this line of experiments. English requests are placed mainly in OOD Evaluation（分布外评测） and should be rejected by BranchChain（分支链） / Confidence-Gated Continuation（置信度守卫式继续）, not learned as English code generation.

## 6. Coarse task_scope（粗粒度任务范围）

task_scope（任务范围） remains coarse:

- programming（编程范围内）;
- reject_non_programming（拒绝非编程）;
- reject_out_of_scope（拒绝越界）.

Detailed unsupported reasons are expressed in later branch layers or the unsupported_reason field. The dataset avoids using language_target=unknown for supported samples.

## 7. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a deterministic local dataset generation and Scale Smoke Benchmark（规模化冒烟基准） experiment.

