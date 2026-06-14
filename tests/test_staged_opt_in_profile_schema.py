from jianmu.self_learning.darwinforge.staged_opt_in_profile_schema import StagedOptInProfileConfig


def test_staged_opt_in_profile_is_explicit():
    cfg = StagedOptInProfileConfig()
    assert cfg.explicitly_opt_in is True
    assert cfg.opt_in_enabled_only_by_explicit_flag is True


def test_staged_opt_in_profile_is_not_default():
    cfg = StagedOptInProfileConfig()
    assert cfg.default_profile is False
    assert cfg.claim_boundary()["production_ready"] is False
