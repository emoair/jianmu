# v0.6.1 BranchChain Curriculum Freezing

This document defines a curriculum-freezing scaffold for JianMu BranchChain
training dynamics. It is a development experiment, not a v0.5 release claim and
not a claim of stable DarwinForge convergence.

## 1. Why Curriculum Freezing

v0.6 connected the minimal DarwinForge loop, but whole-chain evolution remains
unstable:

- Early layers drift while later layers are still learning.
- Good generations appear but are not preserved.
- Whole-path reward can contaminate correct early branches.
- A stable BranchChain should train big branches first, then small branches.

Curriculum freezing introduces staged training: train a large branch layer,
freeze it after stability criteria are met, keep it active during routing, and
then train the next layer.

## 2. Frozen Layer Semantics

A frozen layer:

- participates in routing
- outputs `BranchDecision`
- contributes confidence and evidence
- is not mutated
- does not receive normal weight updates
- can be conditionally unfrozen under hard-case attribution

Frozen does not mean disabled. A frozen layer remains part of the BranchChain.

## 3. Layer Curriculum Order

Default training order:

1. `task_scope`
2. `language_target`
3. `semantic_domain`
4. `support_gate`
5. `arithmetic_family`
6. `structure_policy`
7. `slot_binding_policy`
8. `target_builder`

## 4. Freeze Criteria

`FreezeCriteria`:

- `per_layer_accuracy >= threshold`
- `stability_window >= N generations`
- `missing_proposal_rate <= max_missing`
- `confidence_margin >= min_margin` optional

Toy defaults:

- `accuracy_threshold = 0.90`
- `stability_window = 3`
- `max_missing_rate = 0.05`

Future formal defaults can be stricter:

- `accuracy_threshold = 0.98`
- `stability_window = 5`
- `max_missing_rate = 0.01`

## 5. Conditional Unfreeze

If a frozen layer is attributed as the main source of hard-case failures, it may
temporarily unfreeze.

Conditions:

- `hard_case_layer_error_rate > threshold`
- or downstream `target_ir_exact_match` fails to improve for consecutive
  generations

Temporary unfreeze:

- `unfreeze_generations = 3`
- low mutation rate
- low learning rate
- re-evaluate freeze criteria after the temporary window

## 6. Hall of Fame

Curriculum training must record:

- `best_generation`
- `best_population_snapshot`
- `best_mean_fitness`
- `best_target_ir_exact_match`
- `best_missing_layer_rate`

Reports must show both final metrics and best metrics. Final generation alone is
not enough, because later perturbation can drift away from a good path.

## 7. Non-Claims

- This does not prove stable DarwinForge convergence.
- This does not prove general program synthesis.
- This does not train C source text.
- This does not patch old source code.
- This does not prove AGI, Transformer replacement, or hardware BPU
  implementation.
- This is a curriculum-freezing scaffold for BranchChain training dynamics.

