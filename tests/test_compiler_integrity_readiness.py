from jianmu.self_learning.darwinforge.compiler_integrity_readiness import build_compiler_integrity_readiness


def test_compiler_integrity_readiness_keeps_production_false(tmp_path) -> None:
    payload = {"compiler_integrity_audit_completed": True, "v1_0_8_8_compiler_claim_downgraded": True, "frontend_backend_lane_separated": True, "backend_manifest_contract_passed": True, "opt_display_recovery_passed": True, "backend_validation_passed": True, "backend_replay_passed": True, "default_profile_unchanged": True, "real_promotion_enabled": False, "security_interference_detected_count": 0}
    result = build_compiler_integrity_readiness(tmp_path, payload)
    assert result["recommended_claim_level"] == "compiler_invocation_integrity_repaired_and_validated"
    assert result["production_function_support_completed"] is False
    assert result["redqueen_autonomous_governance_completed"] is False

