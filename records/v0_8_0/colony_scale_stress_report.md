# Colony Scale Stress Probe（根群规模压力探针） Report（报告）

## Scale Summary（规模摘要）
- scales_attempted（尝试规模）: ['small', 'medium', 'large', 'full']
- scales_completed（完成规模）: ['small', 'medium', 'large']
- skipped_scales（跳过规模）: {'full': 'full skipped by bounded runtime policy（受限运行时间策略跳过 full）'}

## Global Beam Trend（全局束趋势）
- global_beam_trend（全局束趋势）: {'small': 0.2933, 'medium': 0.2733, 'large': 0.5017}

## Colony Lifecycle Trend（根群生命周期趋势）
- stable_root_growth_rate_by_scale（稳定根规模增长）: {'small': 62, 'medium': 700, 'large': 1336}
- nourished_root_growth_rate_by_scale（有养分根规模增长）: {'small': 116, 'medium': 136, 'large': 0}

## Toxic Nutrient Trend（毒性养分趋势）
- ood_toxicity_rate_by_scale（分布外毒性率）: {'small': 0.67, 'medium': 0.6667, 'large': 0.67}

## Shadow Promotion Trend（影子晋升趋势）
- shadow_delta_trend（影子增量趋势）: {'small': 0.0, 'medium': 0.0, 'large': 0.0}

## Resource Efficiency（资源效率）
- resource_efficiency（资源效率）: {'small': 0.6642, 'medium': 0.95, 'large': 1.0}
- runtime_per_100_samples（每百样本运行时间）: {'small': 4.5222, 'medium': 13.3576, 'large': 28.9737}

## Bottleneck Diagnosis（瓶颈诊断）
- scale_limited_likely（规模受限可能）: True
- promotion_limited_likely（晋升受限可能）: False
- routing_limited_likely（路由受限可能）: False
- ood_limited_likely（分布外受限可能）: True
- resource_limited_likely（资源受限可能）: False
- diagnosis_summary（诊断摘要）: scale_limited（规模受限） signal: larger scale improved local/global metrics without OOD regression. ood_limited（分布外受限） signal: OOD false accept or toxic nutrient remains high.

## Non-Claims（非主张）
- This does not prove stable RootForge（根铸） convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not prove AGI, Transformer replacement, hardware BPU implementation, or solved arithmetic.
