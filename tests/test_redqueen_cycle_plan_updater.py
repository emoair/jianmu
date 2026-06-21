from jianmu.self_learning.darwinforge.redqueen_cycle_plan_updater import update_cycle_plan


def test_redqueen_cycle_plan_updater_updates_distribution(tmp_path):
    plan = {"category_weights": {"function": 1.0}, "difficulty_levels": {"function": 2}, "active_review_allocations": {"function": 1.0}, "shape_diversity_targets": {"function": False}, "frontier_pressure": {"function": 1.0}, "boundary_recheck_targets": {}, "rollback_recheck_targets": {}, "replay_recheck_targets": {}}
    metrics = {"categories": [{"category": "function", "success_rate": 1.0, "wrong_stdout_rate": 0.0, "timeout_rate": 0.0, "replay_drift_rate": 0.0, "rollback_failure_rate": 0.0, "coverage_gap": 0.0, "repeated_shape_risk": "low"}]}
    result = update_cycle_plan(tmp_path, plan, metrics, 1)
    assert result["next_plan_generated"] is True
    assert result["difficulty_levels"]["function"] == 3
