from jianmu.self_learning.darwinforge.redqueen_underreaction_audit import audit_over_under_reaction


def test_redqueen_overreaction_audit_blocks_zeroing_boundary_review(tmp_path):
    pre = {"categories": [{"category": "default_blocking", "success_rate": 1.0, "wrong_stdout_rate": 0.0, "timeout_rate": 0.0, "review_weight": 1.0, "difficulty_level": 1}]}
    execution = {"actual_review_allocation": {"default_blocking": 1.0}, "actual_difficulty_distribution": {"default_blocking": 1}, "actual_category_distribution": {"default_blocking": 0}}
    result = audit_over_under_reaction(tmp_path, pre, {"categories": []}, execution)
    assert result["boundary_review_zeroed_count"] == 1
    assert result["overreaction_detected"] is True
