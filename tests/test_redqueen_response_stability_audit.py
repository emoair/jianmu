from jianmu.self_learning.darwinforge.redqueen_response_stability_audit import audit_response_stability


def test_redqueen_response_stability_audit_limits_latency():
    cycles = [{"cycle_index": i, "signal_schedule": ["function_call_weak_signal", "mixed_integration_weak_signal"] if i == 6 else []} for i in range(8)]
    result = audit_response_stability(cycles, max_latency_cycles=1)
    assert result["response_latency_max_cycles"] <= 1
    assert result["response_stability_audit_passed"] is True
