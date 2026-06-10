from jianmu.self_learning.darwinforge.shadow_profile_config import build_shadow_profile_config


def test_shadow_profile_config_writes_boundary(tmp_path):
    result = build_shadow_profile_config(tmp_path)
    assert result["default_profile_unchanged"] is True
    assert result["real_promotion_enabled"] is False
    assert result["claim_boundary"]["production_function_support_completed"] is False
