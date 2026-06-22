from jianmu.self_learning.darwinforge.redqueen_response_latency_audit import audit_response_latency


def test_response_latency_audit_passes_one_cycle():
    result = audit_response_latency({"function_response_latency_cycles": 1, "mixed_response_latency_cycles": 1})
    assert result["response_latency_audit_passed"] is True
