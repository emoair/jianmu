# OOD Toxicity Stress & Long-Run Scale Probe（分布外毒性压力与长时规模探针） Report（报告）

## Long-Run Scale Summary（长时规模摘要）
- modes_attempted（尝试模式）: ['large', 'xlarge', 'full']
- modes_completed（完成模式）: ['large']
- partial_or_skipped（部分或跳过）: {'large': 'completed after bounded runtime target（超过受限运行目标后完成）', 'xlarge': 'xlarge skipped because bounded_runtime_sec is below one hour（受限运行时间低于一小时）', 'full': 'full skipped by bounded runtime policy（受限运行时间策略跳过 full）'}

## Global Beam Trend（全局束趋势）
- global_correct_targetir_in_beam_rate（正确目标中间表示在束内率）: 0.5017
- candidate_space_failure_rate（候选空间失败率）: 0.4983

## OOD Toxicity Taxonomy（分布外毒性分类）
- ood_false_accept_by_class（按类误接收）: {'ood_english_sentence': 23, 'ood_unrelated_request': 22, 'unsupported_arithmetic': 22}

## OOD False Accept Analysis（分布外误接收分析）
- most_common_false_accept_reason（最常见误接收原因）: canonicalizer_made_it_look_supported

## Guard / Retention Balance（守卫与保留平衡）
- guard_candidate_count（守卫候选数）: 2
- guard_candidate_accepted_count（接受守卫候选数）: 1
- arithmetic_supported_retention_after_guard（守卫后算术支持保留率）: 1.0

## Root Colony Lifecycle（根群生命周期）
- stable_root_count（稳定根数）: 1239
- nourished_root_count（有养分根数）: 0

## Runtime and Resource Cost（运行时间与资源成本）
- runtime_seconds（运行秒数）: 795.1221
- total_active_roots（总活跃根数）: 1239

## Bottleneck Diagnosis（瓶颈诊断）
- diagnosis_summary（诊断摘要）: promotion_limited（晋升受限） signal: many keep-local colonies but no shadow promotion candidates. routing_limited（路由受限） signal: local colony lifecycle is active while global beam stays flat. ood_limited（分布外受限） signal: OOD false accept or toxic nutrient remains high.

## Non-Claims（非主张）
- This does not prove stable RootForge（根铸） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not prove AGI, Transformer replacement, hardware BPU implementation, or solved arithmetic.
