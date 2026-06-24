from jianmu.self_learning.darwinforge.mirror_redqueen_feedback_loop import audit_feedback_loop


def test_mirror_redqueen_feedback_loop_changes_redqueen_distribution(tmp_path) -> None:
    cycles = [{"mirror": {"mirror_feedback_events": 10, "mirror_disagreement_rate": 0.1}, "redqueen": {"redqueen_adjustment_events_from_mirror": 2, "review_weight_changed_from_mirror": True, "difficulty_changed_from_mirror": True, "shape_diversity_changed_from_mirror": True, "boundary_recheck_changed_from_mirror": True}}]
    result = audit_feedback_loop(tmp_path, cycles)
    assert result["feedback_loop_audit_passed"] is True

