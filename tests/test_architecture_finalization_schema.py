from jianmu.self_learning.darwinforge.architecture_finalization_schema import REDQUEEN_CATEGORIES, RedQueenBootstrapConfig


def test_architecture_finalization_schema():
    config = RedQueenBootstrapConfig()
    assert config.no_model_training is True
    assert config.no_weight_update is True
    assert "structured_recursion" in REDQUEEN_CATEGORIES
