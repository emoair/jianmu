from jianmu.self_learning.darwinforge.runtime_state_consistency import check_runtime_state_consistency


def test_runtime_state_consistency_requires_full_router_root():
    result = check_runtime_state_consistency({}, {}, {}, {}, {}, {}, {}, {"forbidden_field_in_state_count": 0}, "partial")
    assert result["runtime_full_state_consistency_passed"] is False


def test_runtime_state_consistency_passes_when_safe():
    same = {"same_process_reload_passed": True, "no_label_inference_passed": True, "current_supported_retention_rate": 1.0, "overall_ood_false_accept_rate": 0.0, "over_rejection_detected": False}
    cross = {"cross_process_reload_passed": True}
    external = {"overall_ood_false_accept_rate": 0.0}
    multiseed = {"stable_across_seeds": True}
    result = check_runtime_state_consistency(same, {}, {}, same, cross, external, multiseed, {"forbidden_field_in_state_count": 0}, "full_router_root", True)
    assert result["runtime_full_state_consistency_passed"] is True
