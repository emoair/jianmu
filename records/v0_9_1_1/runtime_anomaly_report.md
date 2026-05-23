# Runtime Anomaly Diagnosis

- runtime_anomaly_detected: True
- anomaly_severity: blocking
- likely_cause: v0.9.1 runner generated fixed metric summaries / harness probe records without real per-sample iteration counters
- records_total_runtime_seconds: 0.131871
- reported_total_sample_count: 77000
- actual_total_iterated_count: 0
- xlarge_runtime_plausible: False
- recommended_next_action: run v0.9.1.2 real longrun with mandatory per-sample counters and subprocess traces
