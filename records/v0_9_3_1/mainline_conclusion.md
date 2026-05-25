# v0.9.3.1 Mainline Conclusion

- v0.9.3 claim before: arithmetic_probe_positive_signal
- v0.9.3 claim after: arithmetic_probe_mixed_signal_needs_per_sample_rerun
- recommended_claim_level: signal_not_verified
- leakage_audit_passed: True
- fixed_value_detected: True
- summary_only_detected: True
- baseline_gap_verified: False
- compiler_backend_type: internal_evaluator

The v0.9.3 arithmetic positive signal is not maintained as verified sample-level improvement because the main gain is explainable by a deterministic index-period rule and aggregate records lack per-sample metric provenance.

Still not proven: solved arithmetic, stable convergence, solved OOD, general program synthesis, same-size LLM advantage, safe real promotion, production readiness, real compiler-backed arithmetic.
