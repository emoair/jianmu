# v0.9.3.1 Failure Analysis

- heldout_sample_count: 1000
- boundary_sample_count: 1000
- candidate_hit_before: 0.8
- candidate_hit_after: 0.95
- supported_failed_examples: 50
- false_accept_examples: 0

Failures are dominated by deterministic candidate misses at fixed index periods, not by expression-specific parser or compiler behavior.
Next minimum action: compiler-backed arithmetic audit with per-sample candidate traces.
