from jianmu.self_learning.darwinforge.redqueen_adaptive_curriculum_executor import apply_adaptive_curriculum


def _plan():
    return {
        "category_weights": {"function": 1.0},
        "difficulty_levels": {"function": 2},
        "active_review_allocations": {"function": 1.0},
        "shape_diversity_targets": {"function": False},
        "frontier_pressure": {"function": 1.0},
        "boundary_recheck_targets": {},
        "rollback_recheck_targets": {},
        "replay_recheck_targets": {},
    }


def test_redqueen_adaptive_curriculum_executor_does_not_fake_weak_category():
    metrics = {"categories": [{"category": "function", "success_rate": 1.0, "wrong_stdout_rate": 0.0, "timeout_rate": 0.0, "replay_drift_rate": 0.0, "rollback_failure_rate": 0.0, "coverage_gap": 0.0, "repeated_shape_risk": "low"}]}
    result = apply_adaptive_curriculum(_plan(), metrics, 1)
    assert result["weak_category_detected"] is False
    assert result["no_fake_weak_category_detected"] is True
    assert result["difficulty_levels"]["function"] == 3


def test_redqueen_adaptive_curriculum_executor_boosts_real_weak_category():
    metrics = {"categories": [{"category": "function", "success_rate": 0.9, "wrong_stdout_rate": 0.0, "timeout_rate": 0.0, "replay_drift_rate": 0.0, "rollback_failure_rate": 0.0, "coverage_gap": 0.0, "repeated_shape_risk": "low"}]}
    result = apply_adaptive_curriculum(_plan(), metrics, 1)
    assert result["weak_category_detected"] is True
    assert result["category_weights"]["function"] > 1.0
