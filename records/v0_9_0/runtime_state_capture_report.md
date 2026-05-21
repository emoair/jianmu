# Runtime State Capture & Paper Figure Data Pack（运行时状态捕获与论文图表数据包）

## Runtime State Capture（运行时状态捕获）
- runtime_capture_passed: True
- capture components: branch=True, roots=True, lifecycle=True, nutrient_toxic=True

## Trained Branch Population（训练后分支种群）
- Captured from a live LayerPreservedPopulation runtime object.

## Trained Root Colonies（训练后根群）
- Captured from live RootColony objects with lifecycle buffers.

## Lifecycle / Nutrient / Toxic Memory（生命周期 / 养分 / 毒性记忆）
- Captured as compact runtime event counters and reward/toxicity totals.

## Runtime Full State（运行时完整状态）
- persisted_state_support_level: full_router_root
- missing_for_full_state: []

## Forbidden Field Scan（禁用字段扫描）
- forbidden_field_in_state_count: 0

## Same/Cross-Process Reload（同/跨进程重载）
- same_process_reload_passed: True
- cross_process_reload_passed: True

## External OOD / Multi-Seed Eval（外部 OOD / 多 seed 评估）
- external_ood_false_accept_rate: 0.0
- multi_seed_stable: True

## Paper Figure Data Pack（论文图表数据包）
- paper_figure_data_pack_generated: True
- paper_figures_generated: True

## arXiv Readiness v3
- ready_for_arxiv_technical_report: True
- recommended_claim_level: technical_report_candidate
- blocking_issues: []

## Failure Analysis
- Any missing figure source data is marked as missing rather than filled in.

## Updated Mainline Judgment
- v0.9.0 tests whether runtime-grown router/root state can be captured and replayed without label leakage.

## Non-Claims（非主张）
- Does not claim stable convergence.
- Does not claim solved OOD.
- Does not claim solved arithmetic.
- Does not claim same-size LLM advantage.
- Does not claim safe real promotion.
