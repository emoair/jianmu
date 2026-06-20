from jianmu.self_learning.darwinforge.redqueen_underreaction_audit import audit_over_under_reaction


def test_redqueen_underreaction_audit_blocks_ignoring_weak_category(tmp_path):
    pre = {"categories": [{"category": "function", "success_rate": 0.9, "wrong_stdout_rate": 0.0, "timeout_rate": 0.0, "review_weight": 1.0, "difficulty_level": 1, "coverage_gap": 0.0, "replay_drift_rate": 0.0, "rollback_failure_rate": 0.0}]}
    execution = {"actual_review_allocation": {"function": 1.0}, "actual_difficulty_distribution": {"function": 1}, "actual_category_distribution": {"function": 10}}
    result = audit_over_under_reaction(tmp_path, pre, {"categories": []}, execution)
    assert result["weak_category_not_boosted_count"] == 1
    assert result["underreaction_detected"] is True
