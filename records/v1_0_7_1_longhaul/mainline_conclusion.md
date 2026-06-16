# v1.0.7.1 Controlled Opt-in Longhaul Validation

## What This Version Did
Ran 8-hour longhaul validation for the v1.0.7 staged opt-in profile with heldout, replay, rollback, coverage, accounting, guard heartbeat, and trace pack evidence.

## What This Version Did Not Do
It did not train or update model weights, modify the default profile, enable real promotion, enable official release, claim production support, add natural language, or add a new capability frontier.

## Mainline Result
- longhaul_validation_completed: True
- wall_clock_hours: 8.00003
- heldout_set_created: True
- no_model_training: True
- no_weight_update: True
- default_profile_unchanged: True
- explicit_opt_in_required: True
- real_promotion_enabled: False
- default_blocking_success_rate: 1.0
- malformed_opt_in_blocking_success_rate: 1.0
- function_opt_in_success_rate: 1.0
- array_opt_in_success_rate: 1.0
- function_array_opt_in_success_rate: 1.0
- structured_recursion_opt_in_success_rate: 1.0
- mixed_opt_in_success_rate: 1.0
- opt_out_rollback_success_rate: 1.0
- real_validation_events: 220577
- real_compiler_invocations: 150577
- unique_compile_unit_count: 9896
- coverage_expansion_successful: False
- replay_success_rate: 1.0
- rollback_review_passed: True
- regression_guard_passed: True
- trace_pack_replayable: True
- ready_for_controlled_opt_in_support_candidate_review: True
- production_function_support_completed: False
- production_array_support_completed: False
- production_recursion_support_completed: False
- recommended_claim_level: controlled_opt_in_longhaul_positive_with_coverage_notes
- blocking_issues: []
- required_next_run: Controlled opt-in support candidate review; do not claim production support.

## Still Not Proven
- production function support completed
- production array support completed
- production recursion support completed
- arbitrary project parsing
- formal Turing completeness proof
- solved program synthesis
- production readiness
- natural language layer completed
- safe real promotion
- stable convergence
- solved OOD
- emergence proven
