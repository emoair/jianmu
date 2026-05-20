# Nutrient-Zone Root Colony（养分区根群）

## 1. Why Local Colony Instead of Global Assimilation（为什么局部根群替代全局吸收）

v0.7.7 showed that direct RootFork Global Assimilation（根叉全局吸收） can cause negative transfer: sub-beam rescued paths（子束救援路径） are valuable, but broadcasting them into global BranchChain（全局分支链） weights can pollute routing. A natural root system does not turn every root after one root tip finds water. It proliferates locally near the nutrient source.

## 2. Nutrient Zone（养分区）

A Nutrient Zone（养分区） is a local region described by fork_layer（分叉层）, stable_prefix（稳定前缀）, canonical feature pattern（规范特征模式）, input_mode（输入模式）, structure_policy（结构策略）, slot_binding_policy（槽位绑定策略）, and successful subbeam path signature（成功子束路径签名）. It is not a global rule.

## 3. Root Colony（根群）

Each Nutrient Zone（养分区） owns a Root Colony（根群） with active roots（活跃根）, nourished roots（有养分根）, starving roots（饥饿根）, necrosis candidates（坏死候选）, necrotic archived roots（坏死归档根）, replacement roots（替代根）, and stable roots（稳定根）. Local Root Proliferation（局部根系增殖） is resource gated and does not grow without bound.

## 4. Toxic Nutrient（毒性养分）

Positive nutrients include correct TargetIR（目标中间表示）, expected output match（期望输出匹配）, compile/run success（编译运行成功）, and correct OOD rejection（正确分布外拒绝）. Toxic Nutrient（毒性养分） includes OOD false accept（分布外误接收）, unsupported_arithmetic false accept（不支持算术误接收）, high-confidence wrong TargetIR（高置信错误目标中间表示）, and repeated false accept in the same zone.

## 5. Promotion（晋升）

A colony cannot influence broader priors after one success. Colony Promotion（根群晋升） requires repeated positive nutrient, low toxicity, no held-out eval regression, no OOD false accept increase, sufficient Colony Stability（根群稳定性）, and rollback-safe updates. Otherwise the colony remains local or enters Colony Quarantine（根群隔离）.

## 6. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a local Root Colony（根群） growth and lifecycle scaffold.
