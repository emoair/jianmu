from jianmu.self_learning.darwinforge.redqueen_stability_drift_audit import audit_stability_drift


def _cycle(index, boundary=1.0):
    return {"cycle_index": index, "execution": {"plan_follow_rate": 0.96, "weak_signal_affected_real_correctness": False}, "plan": {"active_review_allocations": {"unsupported_boundary": boundary}}}


def test_redqueen_stability_drift_audit_detects_boundary_zeroing():
    cycles = [_cycle(i) for i in range(8)]
    cycles[3] = _cycle(3, boundary=0.0)
    result = audit_stability_drift(cycles)
    assert result["boundary_review_zeroed_count"] == 1
    assert result["stability_drift_audit_passed"] is False
