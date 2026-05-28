from __future__ import annotations

from jianmu.self_learning.darwinforge.state_budget_memory_guard import run_state_budget_memory_guard
from jianmu.self_learning.darwinforge.state_budget_profile import build_state_budget_profiles


def test_state_budget_memory_guard_blocks_unsafe_full_materialization(tmp_path) -> None:
    profile = build_state_budget_profiles(["state_100M"])[0]
    profile["materialization_level"] = "fully_materialized"
    result = run_state_budget_memory_guard(tmp_path, [profile])
    row = result["profiles"][0]
    assert row["memory_guard_passed"] is False
    assert "hundred_million_cannot_be_fully_materialized_under_guard" in row["memory_guard_blocking_issues"]

