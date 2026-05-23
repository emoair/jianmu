from jianmu.self_learning.darwinforge.real_longrun_readiness import assess_real_longrun_readiness


def test_real_longrun_readiness_requires_large_real():
    result = assess_real_longrun_readiness(
        {
            "real_large_completed": False,
            "real_xlarge_completed": False,
            "mandatory_counter_guard_passed": True,
            "cross_process_real_execution_verified": True,
            "runtime_plausibility_passed": True,
            "supported_retention_rate": 1.0,
            "external_ood_false_accept_rate": 0.0,
            "forbidden_field_in_state_count": 0,
            "synthetic_summary_detected": False,
            "fixed_metric_detected": False,
        }
    )
    assert result["ready_for_real_longrun_claim"] is False


def test_real_longrun_readiness_blocks_synthetic_summary():
    result = assess_real_longrun_readiness(
        {
            "real_large_completed": True,
            "real_xlarge_completed": False,
            "mandatory_counter_guard_passed": True,
            "cross_process_real_execution_verified": True,
            "runtime_plausibility_passed": True,
            "supported_retention_rate": 1.0,
            "external_ood_false_accept_rate": 0.0,
            "forbidden_field_in_state_count": 0,
            "synthetic_summary_detected": True,
            "fixed_metric_detected": False,
        }
    )
    assert result["ready_for_real_longrun_claim"] is False
