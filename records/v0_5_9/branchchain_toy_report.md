# v0.5.9 BranchChain Toy Training Report

This is a toy scaffold for BranchChain training shape correction. It is not a v0.5 release claim.

## Summary

- dataset size: 20
- population size: 128
- generations: 30
- generation 0 mean_reward: -0.695
- final mean_reward: -1.7
- generation 0 branch_path_accuracy: 0.15
- final branch_path_accuracy: 0.0
- generation 0 target_ir_accuracy: 0.35
- final target_ir_accuracy: 0.2

## Curves

- mean_reward: -0.695, -0.195, -1.28, -2.6, -2.6, -2.57, -2.6, -2.6, -2.57, -2.585, -2.57, -1.19, -0.42, -2.6, 0.365, 0.35, 0.35, 0.19, 0.35, 0.19, 0.365, -0.235, -0.265, -0.235, -0.22, -0.54, -0.64, -0.25, -2.6, -2.6, -1.7
- branch_path_accuracy: 0.15, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
- target_ir_accuracy: 0.35, 0.6, 0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 0.5, 0.0, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.55, 0.55, 0.55, 0.55, 0.5, 0.5, 0.55, 0.0, 0.0, 0.2

## Most Common Wrong Branch Decisions

- task_scope:programming -> <missing>: 13
- semantic_domain:arithmetic -> <missing>: 10
- support_gate:supported -> <missing>: 10
- target_builder:canonical_arithmetic_targetir -> <missing>: 10
- slot_binding_policy:surface_number_order -> <missing>: 9
- structure_policy:binary_operation -> <missing>: 6
- language_target:unknown -> <missing>: 6
- task_scope:programming -> non_programming: 5
- support_gate:unsupported -> <missing>: 5
- language_target:C -> <missing>: 4

## Non-Claims

- This does not prove AGI.
- This does not prove Transformer replacement.
- This does not prove hardware BPU implementation.
- This does not prove general program synthesis.
- This does not train C source text.
- This is a training-shape correction from flat classifier to branch-chain routing.
