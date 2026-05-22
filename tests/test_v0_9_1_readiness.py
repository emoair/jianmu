from jianmu.self_learning.darwinforge.v0_9_1_readiness import assess_v0_9_1_readiness


def _summary():
    return {
        "modes_completed": ["quick", "medium", "large"],
        "persisted_state_support_level": "full_router_root",
        "missing_for_full_state": [],
        "forbidden_field_in_state_count": 0,
        "cross_process_reload_passed": True,
        "multi_seed_stable": True,
        "expanded_external_ood_completed": True,
        "external_ood_false_accept_rate": 0.0,
        "supported_retention_rate": 1.0,
        "baseline_harness_generated": True,
        "ablation_harness_generated": True,
        "comparison_data_pack_generated": True,
        "real_promotion_disabled": True,
    }


def test_v0_9_1_readiness_requires_large_completed():
    result = assess_v0_9_1_readiness(_summary())
    assert result["ready_for_v0_9_1_claim"] is True


def test_v0_9_1_readiness_blocks_partial_only():
    summary = _summary()
    summary["modes_completed"] = ["quick"]
    result = assess_v0_9_1_readiness(summary)
    assert result["ready_for_v0_9_1_claim"] is False
    assert "large mode not completed" in result["blocking_issues"]
