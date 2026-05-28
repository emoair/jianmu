# v0.9.16 Training Rerun with Dataset V2 + Chinese Grammar Factory

## Why v0.9.16 exists

v0.9.14 prepared the Turing-frontier dataset v2, v0.9.15 showed that raw LLM free generation collapsed, and v0.9.15.2 established a deterministic Codex/grammar Chinese data factory. v0.9.16 runs a training/profile-learning rerun to test whether the cleaner data improves the layerwise sparse 1B freeze-prune profile.

## Data sources

- v0.9.14 Turing-frontier dataset v2.
- v0.9.15.2 Codex/grammar Chinese dataset.
- Only Chinese current-supported bounded-control samples enter `train_current`.
- Function, array, recursion, unbounded execution, English, and mixed-language samples remain isolated as boundary, future, hard-OOD, or review data.

## Profiles compared

- `current_1B_reference`
- `combined_hot_rebalanced_balanced_sampling_1B`
- `layerwise_sparse_1B_freeze_prune`

## Dataset ablations

- `dataset_v2_only`
- `chinese_factory_only`
- `dataset_v2_plus_chinese_factory_balanced`
- `dataset_v2_plus_chinese_factory_control_heavy`
- `dataset_v2_plus_chinese_factory_stage_balanced`

## Non-claims

This version does not claim Turing completeness, function/array/recursion support, default profile changed, real promotion, production readiness, or solved program synthesis.
