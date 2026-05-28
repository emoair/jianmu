from __future__ import annotations

from jianmu.self_learning.darwinforge.billion_state_access_audit import audit_billion_state_access


def test_billion_state_access_audit_records_touch_ratio(tmp_path) -> None:
    result = audit_billion_state_access(tmp_path, [{"profile_name": "state_1B", "target_state_units": 1_000_000_000, "actual_state_units_allocated": 1_000_000_000, "materialization_level": "lazy_indexed", "sample_count": 1000}])
    row = result["profiles"][0]
    assert row["touch_ratio"] > 0
    assert row["unique_state_units_touched"] > 0


def test_billion_state_access_audit_detects_low_active_usage(tmp_path) -> None:
    result = audit_billion_state_access(tmp_path, [{"profile_name": "state_1B", "target_state_units": 1_000_000_000, "actual_state_units_allocated": 1_000_000_000, "materialization_level": "lazy_indexed", "sample_count": 1000}])
    row = result["profiles"][0]
    assert row["whether_budget_mostly_cold"] is True
    assert result["state_1B_low_active_usage_warning"] is False

