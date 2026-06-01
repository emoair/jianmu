from __future__ import annotations

from jianmu.self_learning.darwinforge.capability_balance_report import build_capability_balance_report


def test_capability_balance_report() -> None:
    report = build_capability_balance_report({"capability_balance_score": 0.96, "old_strong_stage_delta": 0.02, "boundary_false_accept_delta": 0.0, "future_false_accept_delta": 0.0, "english_mixed_accept_delta": 0.0, "function_array_recursion_isolation_delta": 0.0, "dashboard_passed": True})
    assert report["report_passed"] is True
