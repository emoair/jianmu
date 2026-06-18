from jianmu.self_learning.darwinforge.controlled_opt_in_support_schema import ControlledOptInSupportConfig, SUPPORTED_SUBSETS


def test_controlled_opt_in_support_schema():
    config = ControlledOptInSupportConfig()
    assert config.explicit_opt_in_required is True
    assert config.no_model_training is True
    assert "function_array" in SUPPORTED_SUBSETS
    assert sum(config.negative_targets().values()) >= 50_000
    assert sum(config.positive_targets().values()) >= 50_000
