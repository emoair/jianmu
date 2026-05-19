# Canonical Symbol Layer（规范符号层） Report

## Summary（摘要）
- canonicalization_success_rate（规范化成功率）: 1.0
- source_map_coverage（源映射覆盖率）: 1.0
- raw_vs_canonical_targetir_gap（原始输入与规范输入差距）: 0.2471
- Source Map（源映射） coverage: 1.0

## On/Off Comparison（开关对比）
- without canonicalization zh_number_expression_false_reject_rate（关闭规范化中文数字误拒率）: 1.0
- with canonicalization zh_number_expression_false_reject_rate（开启规范化中文数字误拒率）: 0.3638
- without canonicalization zh_number_targetir_exact_match（关闭规范化中文数字 TargetIR 精确匹配）: 0.0
- with canonicalization zh_number_targetir_exact_match（开启规范化中文数字 TargetIR 精确匹配）: 0.3795

## OOD Evaluation（分布外评测）
- ood_rejection_rate（分布外拒绝率）: 0.955
- ood_false_accept_rate（分布外误接收率）: 0.045

## Examples（示例）
| Raw Text（原始文本） | Canonical Text（规范文本） | Exact（精确） |
|---|---|---|
| 三加四 | 3+4 | False |
| 十一减五 | 11-5 | False |
| 负三乘四 | -3*4 | False |
| 十二除以三 | 12/3 | False |
| 三加四乘五 | 3+4*5 | False |
| 括号里三加四再乘五 | (3+4)*5 | False |

## Non-Claims（非主张）
- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a Canonical Symbol Layer（规范符号层） canonicalization experiment, not a convergence claim.
