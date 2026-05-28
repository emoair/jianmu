from __future__ import annotations

from jianmu.self_learning.darwinforge.state_budget_allocator import allocate_state_budget
from jianmu.self_learning.darwinforge.state_budget_memory_guard import run_state_budget_memory_guard
from jianmu.self_learning.darwinforge.state_budget_profile import build_state_budget_profiles


def test_state_budget_allocator_reports_lazy_not_full(tmp_path) -> None:
    profile = build_state_budget_profiles(["state_100M"])[0]
    guard = run_state_budget_memory_guard(tmp_path, [profile])["profiles"][0]
    allocation = allocate_state_budget(profile, guard)
    assert allocation["allocated"] is True
    assert allocation["materialization_level"] == "lazy_indexed"
    assert allocation["peak_memory_bytes"] < profile["estimated_memory_bytes"]

