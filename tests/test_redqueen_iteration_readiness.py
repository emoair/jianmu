from jianmu.self_learning.darwinforge.redqueen_iteration_readiness import build_redqueen_iteration_readiness


def _parts():
    return (
        {"plan_loader_passed": True, "source_plan_loaded": True},
        {"pre_metrics_snapshot_created": True},
        {"plan_execution_passed": True, "plan_execution_completed": True, "iteration_events": 60000, "real_compiler_invocations": 50000, "plan_follow_rate": 0.99, "default_profile_unchanged": True, "real_promotion_enabled": False},
        {"post_metrics_snapshot_created": True},
        {"metric_delta_review_completed": True, "metric_delta_review_passed": True, "weak_category_received_more_review": True, "stable_category_annealed": True, "coverage_gap_category_received_shape_diversity": True, "default_boundary_minimum_review_preserved": True, "unsupported_boundary_minimum_review_preserved": True},
        {"governance_drift_audit_passed": True, "direct_template_path_detected": False, "marker_ir_direct_compile_detected": False, "summary_only_validation_detected": False},
        {"over_under_reaction_audit_passed": True, "overreaction_detected": False, "underreaction_detected": False},
        {"next_plan_v2_generated": True},
    )


def test_redqueen_iteration_readiness_requires_metric_delta(tmp_path):
    parts = list(_parts())
    parts[4] = {"metric_delta_review_completed": True, "metric_delta_review_passed": False}
    result = build_redqueen_iteration_readiness(tmp_path, *parts)
    assert result["recommended_claim_level"] == "redqueen_iteration_positive_with_notes"


def test_redqueen_iteration_readiness_keeps_production_false(tmp_path):
    result = build_redqueen_iteration_readiness(tmp_path, *_parts())
    assert result["redqueen_governance_iteration_1_positive"] is True
    assert result["production_function_support_completed"] is False
    assert result["production_array_support_completed"] is False
    assert result["production_recursion_support_completed"] is False


def test_redqueen_iteration_readiness_keeps_autonomous_governance_false(tmp_path):
    result = build_redqueen_iteration_readiness(tmp_path, *_parts())
    assert result["redqueen_autonomous_governance_completed"] is False
    assert result["ready_for_official_release"] is False


def test_no_expression_oracle_import():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("redqueen_*iteration*.py"))
    assert "expression_oracle" not in text


def test_no_external_api_calls():
    import pathlib

    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in pathlib.Path("jianmu/self_learning/darwinforge").glob("redqueen_*iteration*.py"))
    assert "openai" not in text
    assert "requests." not in text


def test_real_promotion_disabled():
    import pathlib

    text = pathlib.Path("jianmu/self_learning/darwinforge/redqueen_iteration_readiness.py").read_text(encoding="utf-8")
    assert '"real_promotion_enabled": True' not in text
