# v0.9.12.2 Adaptive Layerwise Allocation + Balanced Sampling Probe

v0.9.12 found that a 1B lazy-indexed state budget had positive but diminishing gains and a low active touch ratio. v0.9.12.1 diagnosed the cause as mixed allocation imbalance and dataset activation. v0.9.12.2 combines the hot-rebalanced 1B diagnostic allocation with branch-activation-balanced sampling, then tests a layerwise sparse 1B freeze-prune diagnostic profile.

## Layerwise 1B

Layerwise 1B means each key tree layer has a 1B lazy-indexed logical budget. It is not a neural-network parameter count, not fully materialized, and not a default architecture change. Active access is bounded by memory, lookup, and runtime guards.

## Freeze-Prune

Freeze-prune freezes hot state, prunes cold state, and transfers frozen useful state to the next layer. This is diagnostic only and does not modify JianMu's main architecture.

## Compared Profiles

- current_1B_reference
- hot_rebalanced_1B_reference
- branch_activation_balanced_reference
- combined_hot_rebalanced_balanced_sampling_1B
- layerwise_sparse_1B_freeze_prune

## Non-Claims

This version does not claim Turing completeness, solved program synthesis, production readiness, emergence proven, or profile promotion completed.
