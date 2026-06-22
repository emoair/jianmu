from jianmu.self_learning.darwinforge.redqueen_weak_signal_readiness import build_weak_signal_readiness


def _summary():
    return {"synthetic_signal_honesty_audit_passed": True, "real_compile_lane_passed": True, "distribution_response_audit_passed": True, "multiround_lifecycle_guard_passed": True, "governance_safety_audit_passed": True, "wall_clock_hours": 6, "cycles_completed": 5, "total_events": 130000, "real_compiler_invocations": 90000, "compiler_verified_correctness_rate": 1.0, "weak_signal_is_synthetic": True, "weak_signal_affected_real_correctness": False, "function_weak_signal_response_passed": True, "mixed_weak_signal_response_passed": True, "stable_recursion_annealing_passed": True, "recovery_annealing_audit_passed": True, "default_profile_unchanged": True, "real_promotion_enabled": False, "production_function_support_completed": False, "production_array_support_completed": False, "production_recursion_support_completed": False, "weak_signal_injected": True}


def test_weak_signal_readiness_requires_real_compile_lane_clean(tmp_path):
    s = _summary()
    s["real_compile_lane_passed"] = False
    result = build_weak_signal_readiness(tmp_path, s)
    assert result["recommended_claim_level"] == "redqueen_weak_signal_blocked_by_real_compile_lane"


def test_weak_signal_readiness_keeps_production_false(tmp_path):
    result = build_weak_signal_readiness(tmp_path, _summary())
    assert result["redqueen_controlled_weak_signal_response_positive"] is True
    assert result["production_function_support_completed"] is False
    assert result["redqueen_autonomous_governance_completed"] is False
