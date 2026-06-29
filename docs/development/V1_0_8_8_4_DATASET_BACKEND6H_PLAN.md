# v1.0.8.8.4 Dataset and Backend6h Plan

1. Calibrate active backend thresholds from v1.0.8.8.3 observed MSVC throughput.
2. Build an incremental curriculum dataset with train, heldout, replay, and negative splits.
3. Run RedQueen category weighting and Mirror dataset feedback.
4. Guard against train-heldout leakage.
5. Run true 6h backend validation with OPT active-work display and trace shard caps.
6. Keep production flags false and do not release.
