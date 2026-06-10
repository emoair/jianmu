from jianmu.self_learning.darwinforge.production_profile_dry_run_schema import ProductionProfileDryRunConfig


def test_shadow_profile_is_explicit_opt_in():
    config = ProductionProfileDryRunConfig()
    assert config.explicitly_opt_in is True
    assert config.profile_name == "production_shadow_dry_run_v1_0_6"


def test_shadow_profile_is_not_default():
    config = ProductionProfileDryRunConfig()
    assert config.default_profile is False
    assert config.claim_boundary()["production_ready"] is False
