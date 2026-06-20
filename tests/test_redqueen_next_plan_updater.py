from jianmu.self_learning.darwinforge.redqueen_next_plan_updater import update_redqueen_next_plan


def test_redqueen_next_plan_updater_freezes_promotion(tmp_path):
    result = update_redqueen_next_plan(tmp_path, {"plan": {"category_weights": {"function": 1.0}, "difficulty_levels": {"function": 2}, "active_review_allocations": {"function": 1.0}}}, {"category_deltas": [{"category": "function", "sample_push_change": 1.0}]})
    assert result["next_plan_v2_generated"] is True
    assert result["promotion_frozen"] is True
    assert result["real_promotion_forbidden"] is True
    assert result["production_claim_forbidden"] is True
