# RootFork Sub-Beam Regrowth（根叉子束再生）

## 1. Why RootFork（为什么需要根叉）

v0.7.5 proved that forced BranchPath（强制分支路径） samples can be synthesized by AtomicSynthesis（原子结构合成）, while Free-Beam Evaluation（自由束评测） still failed to place the correct TargetIR（目标中间表示） inside the beam. This means the endpoint is reachable, but free RootForge（根铸） growth cannot find the route.

RootFork Sub-Beam Regrowth（根叉子束再生） keeps the healthy Stable Prefix（稳定前缀）, identifies the likely Fork Point（分叉点）, and opens a local Prefix-Conditioned Sub-Beam（前缀条件子束） near the low-score or pruned layer. The sub-beam is not a forced answer path; it is a wider local regrowth attempt around the suspected routing bottleneck.

## 2. Global Beam vs Sub-Beam（全局束 vs 子束）

Global Beam（全局束） starts at the root and keeps a bounded Branch Beam Size（分支束宽） across the full BranchChain（分支链）.

Sub-Beam（子束） starts from a Stable Prefix（稳定前缀） and regrows from a Fork Point（分叉点）. It still keeps multiple BranchDecision（分支决策） proposals, applies exploration, and grows complete paths to AtomicSynthesis（原子结构合成） and TargetIR（目标中间表示） feedback.

## 3. Teacher-Guided Diagnostic vs Free Evaluation（教师诊断 vs 自由评测）

Teacher-Guided Diagnostic（教师引导诊断） may use target_branch_path（目标分支路径） after the fact to find:

- first_divergence_layer（首个分歧层）
- correct_option_score_by_layer（正确选项逐层分数）
- correct_option_rank_by_layer（正确选项逐层排名）
- first_low_score_correct_layer（首个正确选项低分层）
- first_pruned_correct_layer（首个正确选项被剪层）

Free-Beam Evaluation（自由束评测） must not read target_branch_path（目标分支路径）, target_ir（目标中间表示）, or expected_output（期望输出） during candidate generation. It only evaluates generated paths after synthesis.

Reports therefore separate teacher_subbeam_rescue_rate（教师子束救援率）, free_beam_correct_targetir_in_beam_rate（自由束正确目标中间表示在束内率）, and seeded_free_beam_correct_targetir_in_beam_rate（播种自由束正确目标中间表示在束内率）.

## 4. Scale Ladder（规模阶梯）

v0.7.5 beam failure may come from small beam size, short generations, weak scoring, missing proposals, or a structural routing defect. Scale Ladder（规模阶梯） compares small / medium / large probe settings to see whether correct_targetir_in_beam_rate（正确目标中间表示在束内率） or Sub-Beam Rescue Rate（子束救援率） improves with scale.

If larger scale improves beam or sub-beam recovery, scale_limited_likely（可能受规模限制） is reported. If all tested scales stay at zero, structural_failure_likely（可能结构性失败） is reported.

## 5. OOD Guard Balancing（分布外守卫平衡）

v0.7.5 repaired arithmetic ingress but raised OOD false accept（分布外误接收）. v0.7.6 adds OOD Guard Balancing（分布外守卫平衡） so ood_english（英语分布外）, ood_unrelated（无关分布外）, and unsupported_arithmetic（不支持算术） receive stronger reject-path priors while arithmetic_supported_retention_rate（算术支持保留率） is also reported.

This is a balance probe: it must not restore OOD rejection by rejecting all supported arithmetic inputs.

## 6. Non-Claims（非主张）

- This does not prove stable DarwinForge（达尔文进化炉） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
- This is a RootFork Sub-Beam Regrowth（根叉子束再生） diagnostic and routing-alignment scaffold.
