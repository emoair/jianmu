from jianmu.self_learning.darwinforge.full_state_consistency import check_full_state_consistency


def test_full_state_consistency_requires_full_router_root():
    result = check_full_state_consistency({}, {}, {"no_label_inference_passed": True}, {"cross_process_reload_passed": True}, {"overall_ood_false_accept_rate": 0.0}, {"stable_across_seeds": True}, {"forbidden_field_in_state_count": 0}, "partial")
    assert result["full_state_consistency_passed"] is False


def test_full_state_consistency_detects_metric_degradation():
    result = check_full_state_consistency(
        {"current_supported_retention_rate": 1.0},
        {},
        {"current_supported_retention_rate": 0.5, "no_label_inference_passed": True, "over_rejection_detected": False},
        {"cross_process_reload_passed": True},
        {"overall_ood_false_accept_rate": 0.0},
        {"stable_across_seeds": True},
        {"forbidden_field_in_state_count": 0},
        "full_router_root",
    )
    assert result["full_state_consistency_passed"] is False
