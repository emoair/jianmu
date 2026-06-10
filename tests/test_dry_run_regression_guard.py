from jianmu.self_learning.darwinforge.dry_run_regression_guard import run_dry_run_regression_guard


def test_dry_run_regression_guard_keeps_arithmetic_path(tmp_path):
    result = run_dry_run_regression_guard(tmp_path)
    assert result["arithmetic_path_regression_clean"] is True


def test_dry_run_regression_guard_keeps_default_runtime_unchanged(tmp_path):
    result = run_dry_run_regression_guard(tmp_path)
    assert result["runtime_default_path_unchanged"] is True
    assert result["default_route_to_shadow_profile_detected"] is False
