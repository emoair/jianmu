from jianmu.self_learning.darwinforge.controlled_opt_in_approval_schema import ApprovalGateConfig


def test_controlled_opt_in_approval_schema():
    config = ApprovalGateConfig()
    assert config.no_model_training is True
    assert config.no_weight_update is True
    assert config.explicit_opt_in_required is True
    assert config.positive_samples == 1000
