from jianmu.self_learning.darwinforge.symbiote_mirror_training_probe import mirror_training_with_frozen_trunk


def test_mirror_training_with_frozen_trunk_positive():
    result = mirror_training_with_frozen_trunk()
    assert result["mirror_training_with_frozen_trunk_positive"] is True
    assert result["compiler_verified_correctness_rate"] == 1.0
