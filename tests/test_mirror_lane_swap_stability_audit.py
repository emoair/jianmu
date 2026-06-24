from jianmu.self_learning.darwinforge.mirror_lane_swap_stability_audit import audit_lane_swap_stability


def test_lane_swap_stability_rejects_drift(tmp_path) -> None:
    cycles = [{"execution": {"active_lane": "lane_a", "frozen_lane": "lane_b", "lane_swap_executed": True}}, {"execution": {"active_lane": "lane_b", "frozen_lane": "lane_a", "lane_swap_executed": True}}]
    result = audit_lane_swap_stability(tmp_path, cycles)
    assert result["lane_swap_stability_audit_passed"] is True
    assert result["lane_state_drift_detected"] is False

