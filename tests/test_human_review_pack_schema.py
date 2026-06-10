from jianmu.self_learning.darwinforge.human_review_pack_schema import HumanReviewPackConfig


def test_human_review_pack_schema():
    config = HumanReviewPackConfig()
    assert config.total_review_samples == 300
    assert sum(config.policy_targets().values()) == 300
    assert config.replay_validation_samples == 1000

