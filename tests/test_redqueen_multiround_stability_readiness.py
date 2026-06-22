from jianmu.self_learning.darwinforge.redqueen_multiround_stability_readiness import build_stability_readiness


def _summary():
    return {"msvc_preflight_passed": True, "msvc_fail_fast_test_passed": True, "wall_clock_hours": 8, "cycles_completed": 8, "total_events": 180000, "real_compiler_invocations": 130000, "real_compile_lane_passed": True, "compiler_verified_correctness_rate": 1.0, "stability_drift_audit_passed": True, "response_stability_audit_passed": True, "perturbation_recovery_audit_passed": True, "multiround_lifecycle_guard_passed": True, "governance_safety_audit_passed": True, "default_profile_unchanged": True, "real_promotion_enabled": False, "production_function_support_completed": False, "production_array_support_completed": False, "production_recursion_support_completed": False}


def test_redqueen_multiround_stability_readiness_requires_msvc_preflight(tmp_path):
    s = _summary()
    s["msvc_preflight_passed"] = False
    result = build_stability_readiness(tmp_path, s)
    assert result["recommended_claim_level"] == "msvc_environment_not_ready"


def test_redqueen_multiround_stability_readiness_keeps_production_false(tmp_path):
    result = build_stability_readiness(tmp_path, _summary())
    assert result["redqueen_multiround_stability_positive"] is True
    assert result["production_function_support_completed"] is False
    assert result["redqueen_autonomous_governance_completed"] is False
