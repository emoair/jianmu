# RootFork Global Assimilation（根叉全局吸收）

## 1. Why Global Assimilation（为什么需要全局吸收）

v0.7.6 showed that forced BranchPath（强制分支路径） is reachable, global beam has a small correct_targetir_in_beam_rate（正确目标中间表示在束内率）, and RootFork Sub-Beam Regrowth（根叉子束再生） can rescue failed samples. If rescued paths cannot feed back into the global BranchChain（分支链）, JianMu will remain dependent on local repair. RootFork Global Assimilation（根叉全局吸收） converts Sub-Beam Rescue Memory（子束救援记忆） into global scoring updates.

## 2. Why Slot Binding（为什么重点修槽位绑定）

v0.7.6 identified slot_binding_policy（槽位绑定策略） as the weakest layer: its correct option rank was highest, its correct option score was lowest, and first_low_score_correct_layer（首个正确选项低分层） concentrated there. v0.7.7 therefore repairs surface_number_order（表面数字顺序）, signed_number_order（带符号数字顺序）, chinese_number_order（中文数字顺序）, and slot order confidence alignment（槽位顺序置信对齐） without forcing all canonicalized Chinese inputs onto chinese_number_order.

## 3. Root Lifecycle（根生命周期）

All roots need a lifecycle, not only low-score correct roots. Root Lifecycle Manager（根生命周期管理器） tracks active_root（活跃根）, nourished_root（有养分根）, starving_root（饥饿根）, necrosis_candidate（坏死候选）, necrotic_archived_root（坏死归档根）, replacement_root（替代根）, and stable_root（稳定根）.

High-score correct roots receive Nutrient Signal（养分信号） and move toward stable buffers. Low-score correct roots remain eligible for regrowth. High-score wrong roots are suppressed and may enter necrosis. Low-score wrong roots with healthy prefixes can request Root Replacement（根替代生长）. Necrotic roots are archived as negative memory and do not consume active beam budget.

## 4. Resource-Gated Root Growth（资源门控根系生长）

Root growth is bounded by max_active_roots（最大活跃根数）, max_subbeam_regrowth_per_generation（每代最大子束再生数）, max_replacement_roots_per_generation（每代最大替代根数）, and max_necrosis_archive_size（最大坏死归档大小）. Nourished roots receive more resources; starving roots lose TTL; necrotic archived roots stop consuming active resources.

## 5. OOD Metric Reconciliation（分布外指标口径统一）

v0.7.6 had an OOD conflict between the main report and the scale ladder. v0.7.7 uses OOD Metric Reconciliation（分布外指标口径统一） so ood_false_accept_rate（分布外误接收率） and ood_rejection_rate（分布外拒绝率） share one definition, split, evaluator_name（评测器名称）, guard_state（守卫状态）, population_state（种群状态）, and scale_label（规模标签）.

## 6. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a RootFork Global Assimilation（根叉全局吸收） and Root Lifecycle Manager（根生命周期管理器） scaffold.
