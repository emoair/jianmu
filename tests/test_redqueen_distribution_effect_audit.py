from jianmu.self_learning.darwinforge.redqueen_distribution_effect_audit import audit_distribution_effect


def test_redqueen_distribution_effect_audit_requires_real_distribution_change(tmp_path):
    cycles = [{"execution": {"plan_follow_rate": 0.99}, "next_plan": {"category_weights": {"a": 1}, "difficulty_levels": {"a": i}, "active_review_allocations": {"a": 1}, "shape_diversity_targets": {"a": bool(i)}, "frontier_pressure": {"a": 1+i}, "no_fake_weak_category_detected": True}} for i in [1, 2, 3]]
    result = audit_distribution_effect(tmp_path, {"cycles": cycles})
    assert result["redqueen_controlled_distribution"] is True
    assert result["distribution_effect_audit_passed"] is True
