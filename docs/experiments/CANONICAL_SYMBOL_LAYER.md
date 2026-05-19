# Canonical Symbol Layer（规范符号层）

## 1. Why Canonical Symbol Layer（为什么需要规范符号层）

v0.7.0 Symbol Grounding Curriculum（符号接地课程）尝试让 BranchChain（分支链）通过 Raw Symbol Feature（原始符号特征）和 DarwinForge（达尔文进化炉） reward 自己学会：

- 三 ↔ 3
- 十一 ↔ 11
- 负三 ↔ -3
- 加 ↔ +
- 减 ↔ -
- 乘 ↔ *
- 除以 ↔ /

结果显示 symbol grounding（符号接地）指标仍为 0。这个结果说明，基础符号等价关系更适合放在前置 lexer-like canonicalizer（类似词法分析的规范化器）中处理，而不是强行交给后端路由模型从零学习。

## 2. Not TargetIR parsing（不是 TargetIR 解析）

Canonical Symbol Layer（规范符号层）只允许：

raw_text（原始文本） → canonical_text（规范文本） / Token Stream（令牌流） / Source Map（源映射）

不允许：

- raw_text（原始文本） → TargetIR（目标中间表示）
- raw_text（原始文本） → C source（C 源码）
- raw_text（原始文本） → expression tree（表达式树）

允许：

三加四乘五 → 3+4*5

禁止：

三加四乘五 → add(lit(3),mul(lit(4),lit(5)))

TargetIR（目标中间表示）仍然必须由 BranchChain（分支链）和 AtomicSynthesis（原子结构合成）生成。

## 3. Source Map（源映射）

每次 Symbol Canonicalization（符号规范化）必须保存：

- raw_text（原始文本）
- canonical_text（规范文本）
- token_stream（令牌流）
- source_map（源映射）
- changed
- warnings

```json
{
  "raw_text": "三加二",
  "canonical_text": "3+2",
  "source_map": [
    {"raw": "三", "canonical": "3", "type": "NUM", "span": [0, 1]},
    {"raw": "加", "canonical": "+", "type": "OP_PLUS", "span": [1, 2]},
    {"raw": "二", "canonical": "2", "type": "NUM", "span": [2, 3]}
  ]
}
```

## 4. Engineering boundary（工程边界）

编译器不会让后端优化器自己学习 `+` 是加法。JianMu 也不应该让 BranchChain（分支链）负责最基础的符号等价规范化。

Canonical Symbol Layer（规范符号层）是 input standardization（输入标准化），不是 final semantic generation（最终语义生成）。它不生成 TargetIR（目标中间表示），不生成 C source（C 源码），也不使用 generated output（生成输出）自证正确。

## 5. Evaluation（评测）

v0.7.1 报告以下指标：

- canonicalization_success_rate（规范化成功率）
- source_map_coverage（源映射覆盖率）
- zh_number_false_reject_before_after（中文数字误拒前后）
- zh_number_targetir_exact_match_before_after（中文数字 TargetIR 前后）
- raw_vs_canonical_targetir_gap（原始输入与规范输入差距）
- canonical_input_rejection_rate（规范输入拒绝率）
- OOD Evaluation（分布外评测）

## 6. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a Canonical Symbol Layer（规范符号层） canonicalization experiment, not a convergence claim.

