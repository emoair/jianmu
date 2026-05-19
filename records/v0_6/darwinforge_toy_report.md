# v0.6 DarwinForge Toy Report

This is a minimal DarwinForge scaffold, not a completed system.

## Summary

- dataset size: 20
- population_per_layer: 16
- generations: 30
- top_k_candidates: 3
- compile_checks_per_generation: 8
- generation 0 mean_fitness: 4.3217
- final mean_fitness: 3.9967
- generation 0 target_ir_exact_match_rate: 0.5
- final target_ir_exact_match_rate: 0.55
- generation 0 missing_layer_rate: 0.25
- final missing_layer_rate: 0.2
- hard_case_count: 122

## Fitness Curves

- mean_fitness: 4.3217, 4.3417, 4.1067, 4.5417, 4.4417, 4.5567, 4.8167, 4.8217, 4.5567, 4.4567, 3.9967, 4.3567, 3.9967, 3.9967, 5.09, 5.09, 3.9967, 4.3567, 4.3567, 4.3567, 5.45, 4.3567, 3.9967, 4.3567, 3.9967, 5.09, 3.9967, 3.9967, 4.3567, 5.09, 3.9967
- target_ir_exact_match_rate: 0.5, 0.55, 0.55, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.55, 0.6, 0.55, 0.55, 0.7, 0.7, 0.55, 0.6, 0.6, 0.6, 0.7, 0.6, 0.55, 0.6, 0.55, 0.7, 0.55, 0.55, 0.6, 0.7, 0.55
- missing_layer_rate: 0.25, 0.2, 0.25, 0.15, 0.15, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2

## Most Common Final Wrong Branch Decisions

- language_target:unknown -> C: 6
- support_gate:unsupported -> <missing>: 4
- slot_binding_policy:signed_number_order -> surface_number_order: 3
- slot_binding_policy:chinese_number_order -> surface_number_order: 2
- arithmetic_family:mixed_precedence -> multiplication: 2
- structure_policy:precedence_tree -> binary_operation: 2
- task_scope:programming -> unsupported: 2
- arithmetic_family:addition -> subtraction: 1
- structure_policy:reduce_chain -> binary_operation: 1
- support_gate:unsupported -> supported: 1

## Non-Claims

- This does not prove AGI.
- This does not prove Transformer replacement.
- This does not prove hardware BPU implementation.
- This does not prove general program synthesis.
- This does not train C source text.
- This is a minimal DarwinForge scaffold.
