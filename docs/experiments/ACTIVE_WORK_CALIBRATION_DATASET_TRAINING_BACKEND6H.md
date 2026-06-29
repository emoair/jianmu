# v1.0.8.8.4 Active Work Calibration, Incremental Dataset Training, and 6h Backend Validation

## 1. Why This Version Exists

v1.0.8.8.3 repaired active-work observability, Git lifecycle, and trace shard cap, but failed the short active backend validation because the fixed threshold 20K/45min was too aggressive for observed MSVC throughput.

This version calibrates the backend threshold from observed rate, runs a true 6-hour backend validation, and begins incremental curriculum dataset training while keeping validation strictly heldout and backend-verified.

## 2. What This Version Does

- Calibrates backend throughput.
- Runs true 6h backend validation.
- Expands incremental curriculum dataset.
- Separates training, heldout, replay, and negative boundary lanes.
- Verifies no train-heldout leakage.
- Uses RedQueen to adjust data weights.
- Uses Mirror to compare active/frozen lanes.
- Keeps OPT live active-work display.
- Keeps artifacts outside the worktree.
- Enforces trace shard cap.
- Keeps lifecycle clean.

## 3. What This Version Does Not Do

This version does not claim production support completed, RedQueen autonomous governance completed, official release, natural language layer completed, arbitrary project parsing completed, v1.0.8.8 original compiler claim restored, or training-set self-score as heldout validation.
