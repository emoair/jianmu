from jianmu.self_learning.darwinforge.controlled_opt_in_rollback_review import build_default_rollback_regression_recheck


def test_rollback_review_keeps_default_blocking(tmp_path):
    result = build_default_rollback_regression_recheck(
        tmp_path,
        {"rollback_success_rate": 1.0},
        {"bridge_reachable_without_opt_in_count": 0, "default_blocking_success_rate": 1.0},
    )
    assert result["default_profile_unchanged"] is True
    assert result["default_profile_bridge_leak_detected"] is False
    assert result["opt_in_rollback_passed"] is True
