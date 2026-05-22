# v0.9.1 Large-Scale Full-State Reproduction & Baseline Harness

## 1. Why v0.9.1

v0.9.0 solved the partial-state blocker under a bounded probe: runtime-grown BranchChain population, Root Colony state, lifecycle state, and nutrient/toxic memory were captured as `full_router_root` state and reloaded across process boundaries.

v0.9.1 tests whether that result survives larger modes, more seeds, expanded external OOD slices, and baseline / ablation comparison. It is a credibility reproduction step, not a new architecture direction.

## 2. What v0.9.1 Tests

- large / xlarge `full_router_root` capture
- same-process and cross-process reload
- expanded external OOD evaluation
- multi-seed stability
- runtime, memory, and state-size profile
- baseline harness
- ablation harness
- paper-ready comparison data pack

## 3. Non-Claims

v0.9.1 does not claim:

- stable convergence
- solved OOD
- solved arithmetic
- general program synthesis
- same-size LLM advantage
- safe real promotion
- AGI or Transformer replacement
