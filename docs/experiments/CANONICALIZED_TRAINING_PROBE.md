# Canonicalized Training Probe（规范化输入训练探针）

## 1. Why canonicalized training（为什么需要规范化输入训练）

v0.7.1 Canonical Symbol Layer（规范符号层）证明 Symbol Canonicalization（符号规范化） on/off 有明显差距，但它只是评测探针。

v0.7.2 将 Canonical Symbol Layer（规范符号层）接入训练，测试：

- Raw Input Training（原始输入训练）是否继续卡住；
- Canonical Input Training（规范输入训练）是否能降低 zh_number_expression false reject（中文数字表达误拒）；
- Canonical Input Training（规范输入训练）是否能提高 TargetIR exact match（目标中间表示精确匹配）；
- OOD false accept（分布外误接收）是否因为规范化而升高。

## 2. Raw vs canonical training（原始输入训练 vs 规范输入训练）

raw mode:

```text
features = extract_surface_features(raw_text)
```

canonical mode:

```text
canonical = canonicalize_symbols(raw_text)
features = extract_surface_features(canonical.canonical_text)
```

样本仍保留：

- raw_text（原始文本）
- canonical_text（规范文本）
- Source Map（源映射）
- target_ir_canonical（目标中间表示标签）
- expected_output（期望输出）

target_ir_canonical（目标中间表示标签）和 expected_output（期望输出）只用于 prediction 后的 fitness / evaluation（适应度 / 评测），不作为 candidate generation（候选生成）特征。

## 3. Canonicalization boundary（规范化边界）

Canonical Symbol Layer（规范符号层）只做：

raw_text（原始文本） → canonical_text（规范文本） / Source Map（源映射）

不做：

- raw_text → TargetIR（目标中间表示）
- raw_text → expression tree（表达式树）
- raw_text → C source（C 源码）

## 4. Known risks（已知风险）

- canonicalization（规范化）可能让某些 OOD（分布外）输入更像算术，导致 false accept（误接收）上升；
- parentheses（括号）和 mixed precedence（混合优先级）仍可能失败，因为规范化只解决符号等价，不解决结构理解；
- negative numbers（负数）可能暴露 AtomicSynthesis（原子结构合成）的边界问题；
- raw_vs_canonical improvement（原始与规范输入改进）不等于稳定收敛。

## 5. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a Canonicalized Training Probe（规范化输入训练探针）, not a release claim.

