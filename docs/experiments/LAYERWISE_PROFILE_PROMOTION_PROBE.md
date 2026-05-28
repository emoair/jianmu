# v0.9.13 Layerwise Profile Promotion Probe

## Why v0.9.13 Exists

v0.9.12.2 found the layerwise sparse 1B freeze-prune profile to be the strongest diagnostic profile, and v0.9.12.3 restored clean compiler validation by showing the previous blocker was an environment/toolchain issue rather than a candidate or freeze-prune semantic failure. v0.9.13 therefore runs a shadow promotion probe. It is not real promotion.

## Candidate Profile

The candidate profile is `layerwise_sparse_1B_freeze_prune`: a lazy-indexed logical layerwise 1B budget with freeze-prune transfer. It is not fully materialized and is not a neural-network parameter count.

## Compared Baselines

The probe compares `current_1B_reference`, `combined_hot_rebalanced_balanced_sampling_1B`, and `layerwise_sparse_1B_freeze_prune` on fresh samples.

## Promotion Gates

The probe checks capability, stage regression, boundary/future safety, compiler validation, persistence/cross-process reload, resource overhead, and integrity gates. The gate result can only recommend a later default-profile dry-run; it cannot change the default profile.

## Non-Claims

This version does not enable real promotion, change the default profile, claim Turing completeness, claim solved program synthesis, claim production readiness, or claim emergence proven.
