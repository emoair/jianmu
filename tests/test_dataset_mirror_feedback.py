from jianmu.self_learning.darwinforge.dataset_mirror_feedback import build_mirror_dataset_feedback


def test_dataset_mirror_feedback_adjusts_weights(tmp_path) -> None:
    result = build_mirror_dataset_feedback(tmp_path)
    assert result["mirror_feedback_adjusted_dataset_weights"] is True
    assert result["mirror_feedback_passed"] is True
