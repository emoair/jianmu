from jianmu.self_learning.darwinforge.baseline_execution_trace import audit_baseline_execution, run_real_mini_baseline_trace


def test_baseline_trace_detects_fixed_summary_metrics():
    trace = audit_baseline_execution({"results": [{"baseline_name": "random_router", "runtime_seconds": 0.0}]})
    assert trace["baseline_real_execution_verified"] is False
    assert trace["baselines"][0]["metric_from_fixed_summary"] is True


def test_real_mini_baseline_trace_iterates_samples():
    trace = run_real_mini_baseline_trace([{"sample_id": "a"}, {"sample_id": "b"}])
    assert trace["baseline_real_execution_verified"] is True
    assert trace["baselines"][0]["actual_sample_count"] == 2
