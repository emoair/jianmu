# Tiny Learned Route Classifier Baseline

- train count: 800
- eval count: 200
- route_id labels: 9
- task_family labels: 8

## Majority Baseline

- majority_route_id_accuracy: 0.25
- majority_task_family_accuracy: 0.25
- majority_supported_accuracy: 0.87

## Learned Perceptron

- learned_route_id_accuracy: 0.805
- learned_task_family_accuracy: 0.735
- learned_supported_accuracy: 0.965
- unsupported_precision: 0.9524
- unsupported_recall: 0.7692
- unsupported_f1: 0.8511

## Per Route Accuracy

- append_literal_to_existing_sum: 0.7778
- append_multiple_literals_to_existing_sum: 0.9167
- explicit_expression_rewrite: 0.45
- generate_new_sum_from_text: 0.72
- no_op_keep_existing: 1.0
- replace_operand_by_index: 0.875
- unsupported_expression_input: 0.9444
- unsupported_language_input: 1.0

## Most Common Route Errors

- generate_new_sum_from_text -> explicit_expression_rewrite: 13
- explicit_expression_rewrite -> generate_new_sum_from_text: 11
- append_literal_to_existing_sum -> append_multiple_literals_to_existing_sum: 4
- append_literal_to_existing_sum -> unsupported_language_input: 4
- append_multiple_literals_to_existing_sum -> append_literal_to_existing_sum: 2
- replace_operand_by_index -> unsupported_language_input: 2
- generate_new_sum_from_text -> unsupported_expression_input: 1
- replace_operand_by_index -> replace_last_operand: 1
- unsupported_expression_input -> explicit_expression_rewrite: 1

## Non-Claims

- This does not prove general learned routing.
- This does not generate ProgramIR tokens yet.
- This does not replace the compiler-validated backend.
- This is only a tiny learned route classification baseline.
