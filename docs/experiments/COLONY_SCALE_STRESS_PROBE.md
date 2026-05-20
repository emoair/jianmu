# Colony Scale Stress Probe（根群规模压力探针）

## 1. Why Scale Stress（为什么做规模压力测试）

v0.7.9 Colony Nutrient Activation（根群养分激活）证明 local colony lifecycle（局部根群生命周期）已经启动：Nourished Root（有养分根）、Stable Root（稳定根）、Starving Root（饥饿根）、Necrotic Root（坏死根）和 replacement root（替代根）都能被记录。

但 global beam（全局束）仍未提升。v0.8.0 用更大 train / eval / OOD sample scale（样本规模）、更高 cycle_count（循环数）、更大 Root Colony（根群）预算和更宽 beam（束）来测试当前瓶颈是否只是规模不足。

## 2. Shadow Only（只做影子晋升）

本版禁止 real promotion（真实晋升）。

所有 Shadow Promotion（影子晋升）只在 shadow copy（影子副本）上模拟，不直接修改 global BranchChain（全局分支链）权重，不把 local colony（局部根群）的成功无门控广播到全局。

## 3. Bottleneck Classification（瓶颈分类）

v0.8.0 输出 Bottleneck Diagnosis（瓶颈诊断）：

- scale_limited（规模受限）：规模增加后 global beam（全局束）或 local stability（局部稳定性）明显提升，且 OOD Evaluation（分布外评测）不退化。
- promotion_limited（晋升受限）：Keep-Local Colony（保持局部根群）很多、Stable Root（稳定根）很多，但 shadow promote candidate（影子晋升候选）仍为零。
- routing_limited（路由受限）：Local Colony Evaluation（局部根群评测）活跃，但 global BranchChain（全局分支链）不随规模改善。
- ood_limited（分布外受限）：OOD False Accept Toxicity（分布外误接收毒性）高或随规模增长。
- resource_limited（资源受限）：active roots（活跃根）触达预算，或 Resource-Gated Root Growth（资源门控根系生长）效率显著下降。

## 4. Non-Claims（非主张）

- This does not prove stable RootForge（根铸） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This does not prove arithmetic is solved.
