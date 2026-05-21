# v0.8.9 Full Router/Root State Persistence & Reloaded Boundary Eval

## 1. Why Full State Persistence

v0.8.8 produced strong summary-only reload（摘要级重载）, external OOD（外部分布外）, and multi-seed（多 seed） results, but `persisted_state_support_level = summary_only` remained the main blocker. v0.8.9 audits real router/root runtime state（真实路由/根运行时状态） and attempts to serialize it without changing routing, scoring, synthesis, or inference semantics.

The goal is to move from summary-only audit toward full router/root persisted-state evidence（完整路由/根持久化证据）. If trained runtime objects are not available in records, the run must say so.

## 2. State Inventory

State components are classified as:

- `full_router_state`
- `full_root_state`
- `boundary_probe_state`
- `scoring_state`
- `lifecycle_state`
- `memory_state`
- `evaluation_summary_only`
- `unavailable`

The inventory distinguishes real inference/runtime state（真实推理/运行时状态） from evaluation summaries（评估摘要）. Metrics records are not counted as router/root state.

## 3. Forbidden Fields

Persisted state must not contain these as inference features:

- `boundary_label`
- `expected_action`
- `nutrient_policy` / `toxicity_policy`
- `target_ir`
- `expected_output`
- `target_branch_path`

If the forbidden field scan（禁用字段扫描） finds any of these, the probe must fail.

## 4. Cross-Process Reload

Same-process reload is not enough. v0.8.9 uses an independent Python subprocess（独立 Python 子进程） to load state and run reloaded evaluation. The child process receives only:

- `state_dir`
- `dataset_dir`
- config
- records output dir

The child process must also pass no-label inference guard（无标签推理防泄漏）.

## 5. arXiv Readiness

The readiness output includes:

- `ready_for_arxiv_technical_report`
- `recommended_claim_level`
- `blocking_issues`
- `required_non_claims`
- `suggested_title`
- `suggested_abstract_claim_boundary`

If support level is not `full_router_root`, readiness must remain false.

## 6. Non-Claims

This version does not claim:

- stable convergence
- solved OOD
- solved arithmetic
- general program synthesis
- same-size LLM advantage
- safe real promotion
