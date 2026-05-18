# JianMu Chinese Intent Dataset Alpha

- dataset name: `jianmu_zh_intent_1000`
- version: `v0.5.6-alpha`
- total samples: 1000
- train/eval split: 800 / 200

## Task Family Counts

- append_literal_to_existing_sum: 180
- append_multiple_literals_to_existing_sum: 120
- comparison_prealpha: 50
- explicit_expression_rewrite: 100
- generate_sum_program: 250
- no_op_keep_existing: 100
- replace_operand: 120
- unsupported_input: 80

## Route ID Counts

- append_literal_to_existing_sum: 180
- append_multiple_literals_to_existing_sum: 120
- explicit_expression_rewrite: 100
- generate_new_sum_from_text: 250
- no_op_keep_existing: 100
- replace_last_operand: 24
- replace_operand_by_index: 96
- unsupported_expression_input: 86
- unsupported_language_input: 44

## Supported vs Unsupported

- supported: 870
- unsupported: 130

## Coverage

- Chinese number count: 663
- negative number count: 579
- technical token count: 180
- eval-only template count: 200
- eval unseen number-combination count: 183

## Known Limitations

- The dataset covers a controlled Chinese-first summation/editing slice.
- Comparison samples are pre-alpha labels and are not supported by the current runtime.
- Unsupported samples intentionally have no ProgramIR token sequence.
- ProgramIR token labels are scaffold targets, not generated C source code.

## Non-Claims

- This dataset does not prove learned routing.
- This dataset does not prove general program synthesis.
- This dataset is a controlled Chinese-first intent-to-structure benchmark seed.
- This dataset is not a natural-language generalization benchmark.
