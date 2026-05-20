# Colony Nutrient Activation（根群养分激活）

## 1. Why Activation（为什么需要激活）

v0.7.8 Nutrient-Zone Root Colony（养分区根群）已经建立了局部 Nutrient Zone（养分区）和 Root Colony（根群），但 Root Lifecycle（根生命周期）没有真正启动：Nourished Root（有养分根）、Stable Root（稳定根）、Starving Root（饥饿根）和 Necrotic Root（坏死根）计数都接近零。

v0.7.9 的目标不是提高全局分数，而是让 Local Nutrient Cycle（局部养分循环）先运转起来：有正养分的 Root Tip（根尖）应进入 nourished / stable，无养分的根尖应 starvation / necrosis，有稳定前缀但后缀失败的根应产生 replacement root（替代根）。

## 2. Local Before Global（先局部，后全局）

v0.7.7 RootFork Global Assimilation（根叉全局吸收）显示，粗暴把 sub-beam rescued paths（子束救援路径）广播到 global BranchChain（全局分支链）权重会带来负迁移。

v0.7.9 继续保持局部优先：

- Local Colony Evaluation（局部根群评测）先验证局部根群是否稳定吸收 Nutrient Signal（养分信号）。
- Keep-Local Colony（保持局部根群）是合法中间状态。
- Shadow Promotion（影子晋升）默认只模拟，不实际污染全局 BranchChain（分支链）。
- 只有通过全局非退化和 OOD Evaluation（分布外评测）门控，才允许未来版本考虑真实晋升。

## 3. Toxic Nutrient（毒性养分）

Toxic Nutrient（毒性养分）必须独立记账，不能被正养分抵消为零。

- OOD false accept（分布外误接收）是 OOD False Accept Toxicity（分布外误接收毒性）。
- unsupported arithmetic false accept（不支持算术误接收）是 Toxic Nutrient（毒性养分）。
- high confidence wrong TargetIR（高置信错误目标中间表示）是 Toxic Nutrient（毒性养分）。
- correct OOD rejection（正确分布外拒绝）是正养分。
- correct unsupported rejection（正确不支持拒绝）也是正养分。

v0.7.8 的 `ood_false_accept_toxic_count（分布外误接收毒性数） = 0` 是本版修复目标。

## 4. Keep-Local Colony（保持局部根群）

不是所有未晋升 Root Colony（根群）都应该 Colony Quarantine（根群隔离）。

本版区分：

- promote（晋升）：满足严格晋升条件。
- keep_local（保持局部）：局部有效、低毒，但还不能影响全局。
- quarantine（隔离）：毒性过高或不稳定。
- rollback（回滚）：Shadow Promotion（影子晋升）测试失败。
- reject（拒绝）：无正养分、无稳定前缀、无再生价值。

## 5. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a local colony lifecycle activation scaffold.
