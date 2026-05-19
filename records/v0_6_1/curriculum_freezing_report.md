# v0.6.1 BranchChain Curriculum Freezing Report

This is a training-dynamics scaffold, not a stable convergence claim.

## Final vs Best

- generation 0 mean_fitness: 3.1067
- final mean_fitness: 3.4817
- best mean_fitness: 3.4867
- generation 0 target_ir_exact_match_rate: 0.5
- final target_ir_exact_match_rate: 0.55
- best target_ir_exact_match_rate: 0.55
- generation 0 missing_layer_rate: 0.2
- final missing_layer_rate: 0.0
- best_generation: 3

## Freeze Events

- generation 2: task_scope (freeze_criteria_met)
- generation 5: language_target (freeze_criteria_met)
- generation 6: semantic_domain (freeze_criteria_met)

## Unfreeze Events

- none

## Curves

- active_layer: task_scope, task_scope, task_scope, language_target, language_target, language_target, semantic_domain, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate, support_gate
- mean_fitness: 3.1067, 3.1067, 3.1067, 3.4867, 3.4867, 3.4867, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817, 3.4817
- target_ir_exact_match_rate: 0.5, 0.5, 0.5, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55
- missing_layer_rate: 0.2, 0.2, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0

## Hard-Case Attribution Summary

- arithmetic_family: error_rate=0.15, severity=0.09
- slot_binding_policy: error_rate=0.05, severity=0.03
- structure_policy: error_rate=0.15, severity=0.09
- support_gate: error_rate=0.1, severity=0.1

## Non-Claims

- This does not prove stable DarwinForge convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
