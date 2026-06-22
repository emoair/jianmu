from jianmu.self_learning.darwinforge.time_integrity_readiness import build_time_integrity_readiness


def _payload():
    return {"code_audit_passed_after_fix": True, "repair_validation_passed": True, "v1_0_8_6_endurance_claim_accepted": False, "v1_0_8_6_endurance_claim_downgraded": True, "v1_0_8_6_time_claim_audited": True, "wallclock_timer_contract_passed": True, "heartbeat_contract_passed": True, "time_integrity_guard_passed": True, "actual_elapsed_seconds": 7200, "lifecycle_clean": True, "default_profile_unchanged": True, "real_promotion_enabled": False, "production_function_support_completed": False, "production_array_support_completed": False, "production_recursion_support_completed": False}


def test_time_integrity_readiness_downgrades_unverified_8h_claim(tmp_path):
    result = build_time_integrity_readiness(tmp_path, _payload())
    assert result["recommended_claim_level"] == "time_integrity_repaired_and_short_wallclock_validated"
    assert result["redqueen_multiround_stability_positive"] is False


def test_time_integrity_readiness_keeps_production_false(tmp_path):
    result = build_time_integrity_readiness(tmp_path, _payload())
    assert result["production_function_support_completed"] is False
    assert result["redqueen_autonomous_governance_completed"] is False
