from jianmu.self_learning.darwinforge.symbiote_reward_model import build_symbiote_reward_model


def test_mirror_training_reward_not_trunk_only(tmp_path):
    result = build_symbiote_reward_model(tmp_path)
    assert result["trunk_answer_correctness_is_not_sole_reward"] is True
    assert "structural_truth_mismatch_penalty" in result["mirror_reward_terms"]


def test_symbiote_reward_model_truth_anchors(tmp_path):
    result = build_symbiote_reward_model(tmp_path)
    assert result["compiler_truth_anchor_enabled"] is True
    assert result["structural_truth_anchor_enabled"] is True
    assert result["heldout_generalization_anchor_enabled"] is True
