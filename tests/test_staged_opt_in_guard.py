from jianmu.self_learning.darwinforge.staged_opt_in_config import build_staged_opt_in_config
from jianmu.self_learning.darwinforge.staged_opt_in_guard import run_staged_opt_in_guard


def test_staged_opt_in_guard_blocks_real_promotion(tmp_path):
    profile = build_staged_opt_in_config(tmp_path)
    profile["real_promotion_enabled"] = True
    result = run_staged_opt_in_guard(tmp_path, profile)
    assert result["staged_opt_in_guard_passed"] is False
    assert "real_promotion_off" in result["blocking_issues"]


def test_staged_opt_in_guard_blocks_user_facing_enablement(tmp_path):
    profile = build_staged_opt_in_config(tmp_path)
    profile["user_facing_enabled"] = True
    result = run_staged_opt_in_guard(tmp_path, profile)
    assert result["staged_opt_in_guard_passed"] is False
    assert "user_facing_enablement_false" in result["blocking_issues"]
