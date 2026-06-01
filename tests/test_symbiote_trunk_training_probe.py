from jianmu.self_learning.darwinforge.symbiote_trunk_training_probe import trunk_training_with_frozen_mirror


def test_trunk_not_used_as_sole_truth_verifier():
    result = trunk_training_with_frozen_mirror()
    assert result["top1"] > 0.9224
    assert result["compiler_verified_correctness_rate"] == 1.0
