from jianmu.self_learning.darwinforge.redqueen_real_landing_readiness import build_real_landing_readiness


def _summary():
    return {"endurance_lifecycle_guard_passed": True, "distribution_effect_audit_passed": True, "governance_safety_audit_passed": True, "compiler_verified_correctness_rate": 1.0, "wrong_stdout_count": 0, "frontier_pressure_audit_passed": True, "wall_clock_hours": 6, "cycles_completed": 3, "total_events": 120000, "real_compiler_invocations": 90000, "plan_follow_rate_mean": 0.96, "redqueen_controlled_distribution": True, "adaptive_curriculum_applied": True, "no_fake_weak_category_detected": True, "default_profile_unchanged": True, "real_promotion_enabled": False}


def test_redqueen_real_landing_readiness_requires_6h(tmp_path):
    s = _summary()
    s["wall_clock_hours"] = 1
    result = build_real_landing_readiness(tmp_path, s)
    assert result["recommended_claim_level"] == "failed"


def test_redqueen_real_landing_readiness_keeps_production_false(tmp_path):
    result = build_real_landing_readiness(tmp_path, _summary())
    assert result["redqueen_real_landing_endurance_positive"] is True
    assert result["production_function_support_completed"] is False
