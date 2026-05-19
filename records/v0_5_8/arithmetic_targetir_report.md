# v0.5.8 1M Arithmetic TargetIR Router Baseline

This is a development experiment, not a v0.5 release claim.

## Dataset

- train: 5000
- eval: 1000
- configured parameter budget: 1048576
- hash table params per head: 349525
- compiler sandbox checks: 100

## Baselines

- majority_supported_accuracy: 0.85
- majority_expression_form_accuracy: 0.17
- majority_structure_label_accuracy: 0.17
- oracle_parser_upper_bound: 1.0

The oracle parser is the labeling oracle and deterministic upper bound. The learned router is evaluated as a routing/structure classifier, not as a parser replacement yet.

## Learned Router Metrics

- supported_accuracy: 0.957
- unsupported_precision: 0.8021
- unsupported_recall: 1.0
- unsupported_f1: 0.8902
- expression_form_accuracy: 0.93
- structure_label_accuracy: 0.955
- target_ir_exact_match: 0.805
- expected_output_match: 0.805
- compile_success_rate: 1.0
- run_success_rate: 1.0
- task_success_rate: 0.805
- structure_wrong_but_target_correct: 0

## Most Common Structure Errors

- BIN_ADD -> PAREN_ADD_THEN_MUL: 18
- BIN_DIV -> PAREN_SUB_THEN_DIV: 11
- BIN_MUL -> SUB_THEN_MUL: 7
- ADD_THEN_MUL -> PAREN_ADD_THEN_MUL: 3
- ADD_THEN_MUL -> SUB_THEN_MUL: 2
- BIN_ADD -> BIN_SUB: 1
- SUB_THEN_MUL -> BIN_SUB: 1
- MUL_THEN_ADD -> SUB_THEN_MUL: 1
- BIN_SUB -> SUB_THEN_MUL: 1

## Non-Claims

- This does not prove general program generation.
- This does not train or emit C source text directly.
- This does not patch old C source text.
- This does not replace the compiler-validated backend.
- This does not prove AGI, Transformer replacement, or hardware BPU implementation.
