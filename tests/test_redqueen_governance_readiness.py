from jianmu.self_learning.darwinforge.redqueen_governance_readiness import build_redqueen_governance_readiness


def _parts():
    return (
        {"architecture_finalization_passed": True},
        {"support_scope_codepath_aligned": True},
        {"metrics_bus_created": True, "metrics_bus_read_only": True},
        {"active_review_allocator_completed": True},
        {"difficulty_scheduler_completed": True},
        {"self_governance_policy_passed": True},
        {"redqueen_dry_run_passed": True},
        {"next_validation_plan_generated": True},
    )


def test_redqueen_readiness_requires_architecture_finalization(tmp_path):
    parts = list(_parts())
    parts[0] = {"architecture_finalization_passed": False}
    result = build_redqueen_governance_readiness(tmp_path, *parts)
    assert result["recommended_claim_level"] == "redqueen_blocked_by_architecture_finalization"


def test_redqueen_readiness_keeps_production_support_false(tmp_path):
    result = build_redqueen_governance_readiness(tmp_path, *_parts())
    assert result["redqueen_governance_bootstrap_ready"] is True
    assert result["production_function_support_completed"] is False
    assert result["ready_for_official_release"] is False


def test_no_external_api_calls():
    import pathlib

    text = pathlib.Path("jianmu/self_learning/darwinforge/redqueen_metrics_bus.py").read_text(encoding="utf-8")
    assert "openai" not in text.lower()
    assert "requests." not in text


def test_real_promotion_disabled():
    import pathlib

    text = pathlib.Path("jianmu/self_learning/darwinforge/redqueen_governance_readiness.py").read_text(encoding="utf-8")
    assert '"real_promotion_enabled": True' not in text
