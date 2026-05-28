from jianmu.self_learning.darwinforge.default_profile_config_shadow import build_default_profile_dryrun_config


def test_default_profile_dryrun_real_promotion_disabled(tmp_path):
    cfg = build_default_profile_dryrun_config(tmp_path)
    assert cfg["real_promotion_enabled"] is False


def test_default_profile_actual_default_unchanged(tmp_path):
    cfg = build_default_profile_dryrun_config(tmp_path)
    assert cfg["actual_default_profile_unchanged"] is True
    assert cfg["profile_is_default_runtime"] is False
