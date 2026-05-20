# Wide-Beam Backtracking Search（宽束回溯搜索）

## 1. Why wide beam + backtracking（为什么宽束与回溯要同时存在）

单纯 Wide Branch Beam Search（宽束分支搜索）可以发现更多完整路径，但如果上游层边界本身错了，正确路径可能永远不在 beam（候选束）里。

单纯分层回溯可以修上游边界，但如果每层都要求 100% 冻结，则太保守，容易卡死。

因此 v0.7.3 同时采用：

- Wide Branch Beam Search（宽束分支搜索）
- Conditional Upstream Unfreeze（条件上游解冻）
- Layer Clone Perturbation（层克隆扰动）
- Delayed Path Selection（延迟路径选择）

## 2. Layer Clone（层克隆）

Layer Clone（层克隆）是某一层 BranchNeuron population（分支神经元种群）的临时副本。

clone 来源：

- 复制当前 base layer weights（基础层权重）；
- 加 seeded random perturbation（带种子的随机扰动）；
- 用于生成不同 proposal（候选）；
- 不立即覆盖原层；
- 只有当 clone 在完整路径评估中优于 base，才 promote（提升）。

## 3. Same weights + random perturbation（相同权重 + 随机扰动）

不是重新随机初始化整层，而是：

base weights（基础权重） → clone（克隆） → small/medium/large perturbation（小/中/大扰动） → path search（路径搜索） → full-path reward（完整路径奖励） → promote or discard（提升或丢弃）。

## 4. Delayed Path Selection（延迟路径选择）

不要在早期层立刻只保留最高分路径。

流程是：

L0 beam → L1 beam → L2 beam → complete path ensemble（完整路径集合） → AtomicSynthesis（原子结构合成） → TargetIR（目标中间表示） / expected_output（期望输出） / OOD feedback（分布外反馈） → path-level reward（路径级奖励） → layer clone promotion / pruning（层克隆提升 / 剪枝）。

## 5. Failure taxonomy（失败分类）

1. candidate_space_failure（候选空间失败）
   - beam 中不存在正确 TargetIR（目标中间表示）。

2. ranking_failure（排序失败）
   - beam 中存在正确 TargetIR，但 top-1 不是它。

3. upstream_boundary_failure（上游边界失败）
   - 某个上游层选项持续导致下游无正确路径。

4. synthesis_failure（合成失败）
   - BranchPath（分支路径）看似正确，但 AtomicSynthesis（原子结构合成）无法生成 TargetIR。

## 6. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a Wide-Beam Backtracking Search（宽束回溯搜索） diagnostic and training scaffold.

