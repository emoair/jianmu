# RedQueen Plan Execution Contract

Plan execution must follow the v1.0.8.2 plan fields:

- `category_weights`
- `difficulty_levels`
- `active_review_allocations`
- `shape_diversity_targets`
- `boundary_recheck_targets`
- `rollback_recheck_targets`
- `replay_recheck_targets`

The executor may allocate samples and review budget, but it must not bypass the v1.0.7 staged opt-in profile, the v1.0.6 dry-run adapter, AtomicSynthesis, ExtendedIR, ExtendedEmitterC, or the compiler backend.

Execution records must preserve default profile safety and keep production support flags false.
