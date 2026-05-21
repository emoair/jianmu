# Runtime Training-State Capture & Paper Figure Data Pack

## 1. Why Runtime State Capture（为什么做运行时状态捕获）

v0.8.9 的 blocker 是 partial state, not external OOD or multi-seed behavior. The missing components were explicit: trained branch population, trained root colonies, root lifecycle runtime states, and nutrient/toxic runtime memory.

v0.9.0 captures these components during the probe run rather than reconstructing them afterward from records summaries. This version therefore tests whether the runtime state that actually exists during training can be serialized, reloaded, and evaluated under no-label free-beam conditions.

## 2. State Capture Hooks

The runtime capture layer adds passive hooks:

- `on_branch_population_update`
- `on_root_colony_update`
- `on_lifecycle_update`
- `on_nutrient_toxic_memory_update`
- `on_curriculum_stage_end`
- `on_training_end`

These hooks only record state. They do not alter scoring, routing, synthesis, compiler sandbox behavior, or canonicalization.

## 3. Full Router/Root State Definition

`full_router_root` requires:

- trained_branch_population
- trained_branch_neuron_weights / scores / ranks
- router scoring state
- learned boundary adjustments if available
- trained_root_colonies
- root lifecycle runtime states
- nutrient memory
- toxic memory
- colony memory
- quarantine / future / near-OOD buffers
- curriculum stage deltas
- state hash and schema version

Forbidden inference fields are excluded: `boundary_label`, `expected_action`, `nutrient_policy`, `toxicity_policy`, `target_ir`, `expected_output`, and `target_branch_path`.

## 4. Paper Figure Data Pack

v0.9.0 generates CSV/JSON data and matplotlib figures for:

- scale signal curve
- boundary before/after metrics
- OOD taxonomy distribution
- state persistence support progression
- external OOD and multi-seed stability
- pipeline overview

Figures are generated from records only. Missing source values are marked as missing; curves are not smoothed or cosmetically rewritten.

## 5. Non-Claims

This version does not claim:

- stable convergence
- solved OOD
- solved arithmetic
- general program synthesis
- same-size LLM advantage
- safe real promotion
