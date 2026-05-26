# v0.9.7 Bounded Substrate Training Probe

## Why v0.9.7 exists

v0.9.6 generated and audited the turing-substrate curriculum dataset and ran a
16-worker MSVC compiler validation spot. v0.9.7 starts the training probe on
that dataset. It is still bounded, diagnostic, and explicitly not a
Turing-completeness claim.

## What is trained

The probe updates bounded-substrate state inside JianMu's existing direction:
BranchChain routing priors, Root-Colony lifecycle state, nutrient/toxic memory,
bounded-substrate stage statistics, and candidate-space scoring state.

## What is evaluated

The probe evaluates variables, assignment, statement sequences, `if`/`else`,
bounded `for`, bounded `while` with fuel, nested bounded control, and rejection
of unsupported, trap, future-domain, near-OOD, and hard-OOD samples.

## Forbidden paths

`target_ir`, `expected_output`, `target_branch_path`, `boundary_label`,
`expected_action`, `nutrient_policy`, and `toxicity_policy` are forbidden in
free inference, free-beam candidate generation, and routing. They may only be
used for training supervision or after candidate generation for scoring and
audit. The probe does not use fixed metrics, index-period rules, summary-only
metrics, or compiler result cache replay.

## Non-claims

This version does not claim Turing completeness, solved program synthesis,
solved arithmetic, stable convergence, solved OOD, same-size LLM advantage,
safe real promotion, or production readiness.
