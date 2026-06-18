from jianmu.self_learning.darwinforge.controlled_opt_in_support_readiness import build_controlled_opt_in_support_readiness


def _base():
    scope = {"support_scope_matrix_generated": True}
    unsupported = {"unsupported_boundary_matrix_generated": True}
    taxonomy = {"failure_taxonomy_generated": True}
    negative = {"negative_validation_passed": True, "negative_validation_events": 50_000, "unsafe_compile_invoked_count": 0, "bridge_reachable_without_opt_in_count": 0}
    positive = {"positive_validation_passed": True, "positive_validation_events": 50_000, "real_compiler_invocations": 40_000}
    rollback = {"default_profile_unchanged": True, "explicit_opt_in_required": True, "default_profile_bridge_leak_detected": False, "real_promotion_enabled": False, "user_facing_enabled": False, "official_release_enabled": False, "opt_in_rollback_passed": True, "regression_guard_passed": True}
    trace = {"trace_pack_generated": True, "trace_pack_replayable": True}
    reviewer = {"reviewer_support_pack_generated": True}
    return scope, unsupported, taxonomy, negative, positive, rollback, trace, reviewer


def test_controlled_support_readiness_requires_negative_clean(tmp_path):
    parts = list(_base())
    parts[3] = {**parts[3], "negative_validation_passed": False}
    result = build_controlled_opt_in_support_readiness(tmp_path, *parts)
    assert result["recommended_claim_level"] == "controlled_support_blocked_by_negative_boundary"


def test_controlled_support_readiness_requires_positive_clean(tmp_path):
    parts = list(_base())
    parts[4] = {**parts[4], "positive_validation_passed": False}
    result = build_controlled_opt_in_support_readiness(tmp_path, *parts)
    assert result["recommended_claim_level"] == "controlled_support_blocked_by_positive_validation"


def test_controlled_support_readiness_keeps_production_support_false(tmp_path):
    result = build_controlled_opt_in_support_readiness(tmp_path, *_base())
    assert result["controlled_opt_in_support_candidate_ready"] is True
    assert result["production_function_support_completed"] is False
    assert result["production_array_support_completed"] is False
    assert result["production_recursion_support_completed"] is False
    assert result["ready_for_official_release"] is False
