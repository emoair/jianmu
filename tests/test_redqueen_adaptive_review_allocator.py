from jianmu.self_learning.darwinforge.redqueen_adaptive_review_allocator import allocate_active_review


def test_redqueen_active_review_allocator_weights_weak_category_higher(tmp_path):
    metrics = {"categories": [
        {"category": "weak", "success_rate": 0.9, "wrong_stdout_rate": 0, "timeout_rate": 0, "replay_drift_rate": 0, "rollback_failure_rate": 0, "coverage_gap": 0},
        {"category": "stable", "success_rate": 1.0, "wrong_stdout_rate": 0, "timeout_rate": 0, "replay_drift_rate": 0, "rollback_failure_rate": 0, "coverage_gap": 0},
    ]}
    result = allocate_active_review(tmp_path, metrics)
    assert result["category_review_weights"]["weak"] > result["category_review_weights"]["stable"]
