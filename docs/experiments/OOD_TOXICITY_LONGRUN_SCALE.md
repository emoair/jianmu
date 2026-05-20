# OOD Toxicity Stress & Long-Run Scale Probe（分布外毒性压力与长时规模探针）

## 1. Why OOD Toxicity（为什么研究分布外毒性）

v0.8.0 Colony Scale Stress Probe（根群规模压力探针）显示，scale（规模）可以提升 global beam（全局束）和 stable roots（稳定根），但 OOD toxicity（分布外毒性）几乎不变。

这说明规模可以帮助 supported path（支持路径）进入候选空间，但不会自动学会拒绝 unsupported / OOD（不支持 / 分布外）输入。OOD Guard（分布外守卫）必须作为独立压力系统研究。

## 2. OOD Toxicity Taxonomy（分布外毒性分类）

本版 OOD Toxicity Taxonomy（分布外毒性分类）至少包含：

- ood_english_sentence（英文句子分布外）
- ood_unrelated_request（无关请求）
- unsupported_arithmetic（不支持算术）
- non_exact_division（非整除）
- division_by_zero（除零）
- unsupported_depth（超深表达式）
- unsupported_operator（不支持运算符）
- mixed_language_query（混合语言查询）
- instruction_not_programming（非编程指令）
- malformed_expression（畸形表达式）

## 3. Guard vs Retention（守卫与保留）

目标不是简单拒绝更多输入。

必须同时保持：

- OOD false accept（分布外误接收）下降；
- arithmetic_supported_retention_rate（算术支持保留率）不下降；
- supported global beam（支持样本全局束）不显著退化。

Guard candidate（守卫候选）只能是局部、小步、可回滚的 shadow evaluation（影子评估），不能污染 global BranchChain（全局分支链）。

## 4. Long-Run Scale（长时规模）

允许小时级验证，但必须：

- 每个 run 有 run_id；
- 每个 scale 有 runtime_seconds；
- 每个 run 可独立复现；
- full / xlarge 可因 bounded runtime（受限运行时间）跳过；
- 跳过必须记录 skip_reason。

## 5. Non-Claims（非主张）

- This does not prove stable RootForge（根铸） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This does not prove arithmetic is solved.
