from jianmu.self_learning.darwinforge.redqueen_governance_dry_run import build_next_validation_plan, run_redqueen_governance_dry_run


def test_redqueen_governance_dry_run_reuses_existing_adapter(tmp_path):
    result = run_redqueen_governance_dry_run(
        tmp_path,
        {"metrics_bus_read_only": True},
        {"active_review_allocator_completed": True, "category_review_weights": {}},
        {"difficulty_scheduler_completed": True},
        events=10,
        workers=4,
        compiler_workers=3,
    )
    assert result["adapter_reuses_v1_0_6_dry_run_adapter"] is True
    assert result["redqueen_dry_run_passed"] is True
    assert result["workers_requested"] == 4
    assert result["workers_used"] == 4
    assert result["compiler_workers_requested"] == 3
    assert result["compiler_workers_used"] == 3
    assert result["downgrade_reason"] == ""


def test_redqueen_governance_dry_run_keeps_production_false(tmp_path):
    result = run_redqueen_governance_dry_run(tmp_path, {"metrics_bus_read_only": True}, {"active_review_allocator_completed": True, "category_review_weights": {}}, {"difficulty_scheduler_completed": True}, events=10)
    assert result["real_promotion_enabled"] is False
    assert result["production_support_flags_false"] is True


def test_redqueen_next_validation_plan_generated(tmp_path):
    result = build_next_validation_plan(tmp_path, {"category_review_weights": {"function": 1.0}}, {"schedule": [{"category": "function", "next_difficulty_level": 2, "shape_diversity_push": False}]})
    assert result["next_validation_plan_generated"] is True
    assert result["production_claim_forbidden"] is True
