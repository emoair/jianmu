# v0.5.8 1M Arithmetic TargetIR Router Baseline

This is a development experiment, not a JianMu v0.5 release claim.

The goal is to test whether a pure-Python hashed perceptron branch table with an
approximately 1M-parameter budget can learn a controlled Chinese-first mapping:

```text
Chinese arithmetic intent
-> canonical Arithmetic TargetIR structure
-> deterministic full C program regeneration
-> compiler sandbox validation
```

This experiment does not train on C source text. It does not patch old source
code. It follows Canonical TargetIR Regeneration: the latest intent is mapped to
a normalized target tree, and the full program is regenerated from that tree.

## Scope

- Supported operators: `+`, `-`, `*`, `/`
- Supported literals: Arabic integers, limited Chinese numerals, and controlled
  negative literals
- Supported grouping: parentheses
- Division is accepted only when integer division is exact
- Non-exact division and division by zero are unsupported

## Model Shape

The learned component is a hashed multiclass perceptron. It predicts:

- supported vs unsupported
- expression form
- structure/action label

Numeric slots are extracted deterministically. The learned router is therefore a
structure router, not a C code generator.

## Baselines

- Majority baseline
- Deterministic oracle parser upper bound
- 1M-parameter hashed perceptron router

The oracle parser is the labeling oracle and deterministic upper bound. The
learned router is evaluated as a routing/structure classifier, not as a parser
replacement yet.

## Primary Metrics

- `target_ir_exact_match`
- `compile_success_rate`
- `run_success_rate`
- `expected_output_match`
- `task_success_rate`

`route_id` accuracy is not the central metric in this experiment. TargetIR is
the primary correctness object.

## Non-Claims

- This does not prove general program generation.
- This does not prove broad natural-language understanding.
- This does not prove AGI.
- This does not prove replacement of Transformer models.
- This does not prove hardware BPU implementation.
- This does not replace compiler validation.

