# v0.5.9 BranchChain Training Charter

This document defines the v0.5.9 development correction from flat label
classification toward layered BranchChain training. It is a development charter,
not a JianMu v0.5 release claim.

## Why v0.5.8 Is Insufficient

v0.5.8 is an oracle-assisted flat hashed classifier.

It classifies `supported`, `expression_form`, and `structure_label` with
independent heads. It does not train a hierarchical BranchChain. Its inference
path also uses oracle-assisted feature and slot extraction through the
controlled expression parser. That makes it useful as a calibration experiment,
but not the intended JianMu training model.

The main lesson is architectural: a high structure-label score is not enough.
JianMu needs layered branch decisions, path-level reward, and Canonical TargetIR
Regeneration.

## BranchChain Definition

`BranchDecision`:

- `layer_name`
- `candidates`
- `selected`
- `confidence`
- `neuron_id`
- `evidence`
- `reward`

`BranchPath`:

- `decisions: list[BranchDecision]`
- `route_confidence`
- `atomic_experts`
- `target_builder`
- `early_exit`
- `unsupported_reason`

The path is the trainable object. A route id can remain a convenience label, but
it is not the primary target.

## Layered Branch Topology

Initial topology:

L0 `task_scope`

- `programming`
- `non_programming`
- `unsupported`

L1 `language_target`

- `C`
- `unknown`

L2 `semantic_domain`

- `arithmetic`
- `comparison_future`
- `unsupported`

L3 `support_gate`

- `supported`
- `unsupported`

L4 `arithmetic_family`

- `addition`
- `subtraction`
- `multiplication`
- `exact_division`
- `mixed_precedence`
- `parentheses`
- `unsupported`

L5 `structure_policy`

- `binary_operation`
- `reduce_chain`
- `precedence_tree`
- `parenthesized_tree`
- `unsupported`

L6 `slot_binding_policy`

- `surface_number_order`
- `chinese_number_order`
- `signed_number_order`
- `previous_targetir_delta`
- `unsupported`

L7 `target_builder`

- `canonical_arithmetic_targetir`
- `canonical_program_targetir`
- `early_exit`

## Training Principle

The training target is not a final `route_id`.

The training target is:

```text
branch_path + TargetIR correctness
```

`route_id` is only an intermediate convenience label. TargetIR exact match and
expected output match are primary. The compiler sandbox validates and rewards
the regenerated program; it is not a source generation mechanism.

The intended execution path is:

```text
latest Chinese intent
-> layered BranchChain routing
-> canonical TargetIR / ProgramIR
-> deterministic full program regeneration
-> compiler sandbox validation
-> TraceCache / RouteMemory / QTable feedback
```

## Oracle Boundary

Forbidden during inference:

- `parse_controlled_expression`
- `expression_oracle`
- reading `target_ir` label
- reading `expected_output`
- using generated output as expected output

Allowed:

- dataset label generation
- eval ground truth
- oracle upper bound baseline

Inference may use only `input_text`, optional previous TargetIR, surface
features, learned branch weights, and AtomicExpert/TargetIR builder components.

## Reward Model

Path-level reward:

- `+1.0` target_ir_exact_match
- `+0.5` expected_output_match
- `+0.3` compile_success
- `+0.3` run_success
- `+0.4` correct unsupported early exit
- `-1.0` supported input incorrectly rejected
- `-1.0` unsupported input incorrectly generated
- `-0.7` invalid TargetIR
- `-0.5` wrong TargetIR
- `-0.3` wrong branch decision

Each `BranchDecision` receives a share of the path reward. A depth discount may
be applied:

```text
decision_reward = path_reward * gamma^layer_index
```

## Mutation / Perturbation

Mutation operators:

- branch weight plus or minus a small integer
- neuron threshold plus or minus a small integer
- layer option swap
- expert selection mutation
- random immigrant path
- elite preservation

The goal is not high toy accuracy. The goal is to demonstrate that path choices
can be rewarded, perturbed, retained, and replayed.

## Evaluation Metrics

Required metrics:

- `branch_path_exact_match`
- `per_layer_accuracy`
- `early_exit_precision`
- `early_exit_recall`
- `target_ir_exact_match`
- `expected_output_match`
- `compile_success_rate_checked`
- `run_success_rate_checked`
- `full_eval_compile_success_rate` optional
- `path_reward_mean`
- `reward_improvement_over_generations`

## Non-Claims

- This does not prove AGI.
- This does not prove Transformer replacement.
- This does not prove hardware BPU implementation.
- This does not prove general program synthesis.
- This does not train C source text.
- This is a training-shape correction from flat classifier to branch-chain
  routing.

