# v0.9.21.1 MirrorForge Abstraction Robustness Probe

## Why v0.9.21.1 Exists

v0.9.21 showed that code/AST/IR-derived MirrorToken can act as a strong JianMu-readable teacher layer. That positive result still leaves an important question: whether MirrorToken is too answer-shaped or too close to raw `target_ir` to be useful as a future natural-language alignment target.

v0.9.21.1 is a diagnostic probe for abstraction, field ablation, perturbation robustness, IR-similarity risk, and future NL-to-MirrorToken readiness.

## MirrorToken Abstraction Levels

- `lossless_mirror_token`: the v0.9.21 token view, kept as the reference teacher.
- `semantic_mirror_token`: preserves semantic slots while reducing op-like field names.
- `compressed_mirror_token`: keeps the same semantic content with compact aliases and separators.
- `minimal_mirror_token`: keeps only necessary semantic markers and is allowed to lose reversibility.
- `noisy_mirror_token`: applies synonym replacement and harmless formatting perturbations.

## Field Ablation

The probe removes or masks individual semantic fields to identify which fields actually matter for correctness and which fields can be simplified for a future NL-facing target schema. The critical fields are expected to include update order, loop bounds, condition operators, output variables, and initial values.

## Robustness

The robustness suite checks whether synonym token replacement, variable renaming, local reordering, expanded forms, compressed one-line forms, separator variation, equivalent phrase tokens, and minor noise preserve usable semantics.

## Non-Claims

This version does not implement a natural-language layer. It does not add production capability, does not change the default profile, does not enable real promotion, and does not claim Turing completeness or solved program synthesis.
