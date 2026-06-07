from jianmu.self_learning.darwinforge.production_bridge_scale_readiness import build_production_bridge_scale_readiness


def test_readiness_requires_no_template_bypass_for_positive(tmp_path):
    reaudit = {"phase_a_passed": True, "template_bypass_detected": False, "phase_a_blocking_issues": []}
    scale = _clean_scale()
    result = build_production_bridge_scale_readiness(tmp_path, reaudit, scale)
    assert result["recommended_claim_level"] == "extended_bridge_scale_positive"


def test_readiness_keeps_production_support_false(tmp_path):
    result = build_production_bridge_scale_readiness(tmp_path, {"phase_a_passed": True}, _clean_scale())
    assert result["production_function_support_completed"] is False
    assert result["production_array_support_completed"] is False
    assert result["production_recursion_support_completed"] is False
    assert result["ready_for_official_release"] is False


def test_real_promotion_disabled(tmp_path):
    result = build_production_bridge_scale_readiness(tmp_path, {"phase_a_passed": True}, _clean_scale())
    assert result["ready_for_official_release"] is False


def _clean_scale():
    return {
        "phase_b_started": True,
        "phase_b_completed": True,
        "wall_clock_hours": 4.0,
        "real_compiler_invocations": 25000,
        "all_policy_categories_represented": True,
        "cached_result_used_as_new_count": 0,
        "duplicate_invocation_id_count": 0,
        "stubbed_validation_detected": False,
        "summary_only_validation_detected": False,
        "syntax_filter_used_as_correctness_evidence": False,
        "wrong_stdout_count": 0,
        "timeout_count": 0,
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
    }

