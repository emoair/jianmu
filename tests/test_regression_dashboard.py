from __future__ import annotations

from jianmu.self_learning.darwinforge.regression_dashboard import build_regression_dashboard


def test_regression_dashboard() -> None:
    result = build_regression_dashboard({"top1_after": 0.9042})
    assert result["dashboard_passed"] is True
    assert result["not_training_interceptor"] is True
