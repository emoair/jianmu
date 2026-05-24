from jianmu.self_learning.darwinforge.arithmetic_training_readiness import assess_arithmetic_training_readiness


def test_arithmetic_training_readiness_no_solved_claim():
    result = assess_arithmetic_training_readiness({
        "modes_completed": ["quick", "small"],
        "forbidden_field_access_count": 0,
        "mandatory_counter_guard_passed": True,
        "persisted_state_support_level": "full_router_root",
        "cross_process_reload_passed": True,
        "supported_candidate_hit_before": 0.8,
        "supported_candidate_hit_after": 1.0,
        "heldout_supported_success_rate": 1.0,
        "division_by_zero_false_accept_rate": 0.0,
        "future_domain_supported_accept_rate": 0.0,
        "synthetic_summary_detected": False,
        "fixed_metric_detected": False,
    })
    assert result["ready_for_arithmetic_probe_claim"] is True
    assert result["recommended_claim_level"] == "arithmetic_probe_positive_signal"
    assert result["no_solved_arithmetic_claim"] is True
