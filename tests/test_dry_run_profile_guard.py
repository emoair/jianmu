from jianmu.self_learning.darwinforge.dry_run_profile_guard import run_dry_run_profile_guard
from jianmu.self_learning.darwinforge.shadow_profile_config import build_shadow_profile_config


def test_dry_run_guard_blocks_real_promotion(tmp_path):
    profile = build_shadow_profile_config(tmp_path)
    profile["real_promotion_enabled"] = True
    result = run_dry_run_profile_guard(tmp_path, profile)
    assert result["dry_run_profile_guard_passed"] is False
    assert "real_promotion_off" in result["blocking_issues"]


def test_dry_run_guard_blocks_user_facing_enablement(tmp_path):
    profile = build_shadow_profile_config(tmp_path)
    profile["user_facing_enabled"] = True
    result = run_dry_run_profile_guard(tmp_path, profile)
    assert result["dry_run_profile_guard_passed"] is False
    assert "user_facing_enablement_false" in result["blocking_issues"]
