# RootForge Growth Dynamics（根铸生长动力学）

## 1. Why RootForge Growth Dynamics（为什么需要根铸生长动力学）

v0.7.3 Wide-Beam Backtracking Search（宽束回溯搜索） showed that wider BranchChain（分支链） beams and Layer Clone（层克隆） perturbation can run complete path diagnostics, but the correct TargetIR（目标中间表示） still did not enter the beam.

That result points to Candidate Space Failure（候选空间失败） more than Ranking Failure（排序失败）. Before reinforcing or pruning roots, JianMu must first repair the candidate space:

- AtomicSynthesis（原子结构合成） must support literal-only TargetIR（字面量目标中间表示） such as `lit(-6)` and `lit(49)`.
- AtomicSynthesis（原子结构合成） must cover selected precedence patterns（优先级结构） and parenthesized patterns（括号结构） already present in the v0.7.0 dataset.
- Canonical Symbol Layer（规范符号层） must strip dataset artifact suffixes（数据集伪影后缀） such as `（jm-v070-002202）` without changing raw_text（原始文本）.
- Full Path Diagnostics（完整路径诊断） must treat optional `support_gate=supported` as compatible when target_branch_path（目标分支路径） omits that compatibility layer.

## 2. Root Candidate（根候选）

A RootCandidate（根候选） is a complete BranchPath（分支路径） plus its phenotype and feedback after AtomicSynthesis（原子结构合成） and validation. It carries:

- raw_text（原始文本）
- canonical_text（规范文本）
- BranchPath（分支路径）
- TargetIR（目标中间表示） phenotype
- fitness（适应度）
- Nutrient Signal（养分信号）
- stable_prefix（稳定前缀）
- first_wrong_layer（首个错误层）
- regrowth_fork_point（再生分叉点）
- necrosis_state（坏死状态）

RootForge（根铸） does not patch source text and does not train C source characters. It keeps the Canonical TargetIR Regeneration（规范化目标 IR 重生成） route.

## 3. Nutrient Signal（养分信号）

Nutrient Signal（养分信号） is feedback after prediction. It may use TargetIR exact match（目标中间表示精确匹配）, expected_output match（期望输出匹配）, compiler feedback（编译器反馈）, and correct OOD rejection（正确分布外拒绝）.

It is forbidden during candidate generation. target_ir（目标中间表示标签）, expected_output（期望输出标签）, and target_branch_path（目标分支路径标签） are only post-generation reward and diagnostics.

## 4. Viability Diagnosis（可生性诊断）

Low-score correct roots（低分正确根） are not blindly reinforced. RootForge（根铸） classifies them:

1. Undervalued Correct Root（被低估正确根）
   - correct TargetIR（目标中间表示正确）
   - long stable prefix（稳定前缀长）
   - late or absent first wrong layer（首个错误层晚或不存在）
   - can be promoted into stable buffers

2. Lucky Correct Root（幸运正确根）
   - correct TargetIR（目标中间表示正确）
   - low internal stability
   - early confidence collapse（早期置信崩塌）
   - should trigger Nutrient-Guided Regrowth（养分引导再生） rather than direct full-path reinforcement

3. Unstable Correct Root（不稳定正确根）
   - correct once but cannot reproduce under perturbation
   - enters observation and then Necrosis Queue（坏死队列）

4. Alternative Valid Root（替代有效根）
   - different from the dominant path but repeatedly correct
   - preserved as an alternative root（副根） for later evaluation

## 5. Nutrient-Guided Regrowth（养分引导再生）

Nutrient-Guided Regrowth（养分引导再生） starts from a Stable Prefix（稳定前缀）. It finds a Regrowth Fork Point（再生分叉点） from:

- the end of stable_prefix（稳定前缀）
- the layer before first confidence collapse（首个置信崩塌前一层）
- the layer before divergence from high-score wrong roots（高分错误根分歧点前一层）

From that point, RootForge（根铸） creates Layer Clone（层克隆） populations, applies Weight Perturbation（权重扰动）, and grows new complete paths. The old low-score correct root is observed first; only roots that repeatedly receive Nutrient Signal（养分信号） are strengthened.

## 6. Root Necrosis（根系坏死）

Root Necrosis（根系坏死） handles paths that repeatedly receive no nutrients:

- high-score wrong roots（高分错误根）
- false accepts for unsupported input（误接收不支持输入）
- lucky correct roots（幸运正确根） that cannot reproduce
- roots replaced by regrowth（再生替代根）

Necrosis Queue（坏死队列） is not immediate deletion. Early phase decays scores, middle phase lowers exploration probability, and late phase enables Annealed Pruning（退火枝剪）.

## 7. Annealed Pruning（退火枝剪）

Annealed Pruning（退火枝剪） changes search pressure over time:

- early phase（早期）: high beam size（高束宽）, high perturbation（高扰动）, low pruning（低剪枝）
- middle phase（中期）: medium beam（中束宽）, medium perturbation（中扰动）, necrosis decay（坏死衰减）
- late phase（后期）: lower beam（低束宽）, low perturbation（低扰动）, stronger pruning（强剪枝）

This is a scaffold for growth dynamics, not a claim of convergence.

## 8. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a RootForge Growth Dynamics（根铸生长动力学） scaffold for candidate-space repair, nutrient feedback, regrowth, necrosis, and annealed pruning.
