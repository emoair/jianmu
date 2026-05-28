from __future__ import annotations

from jianmu.self_learning.darwinforge.billion_state_allocator import allocate_billion_state_budget
from jianmu.self_learning.darwinforge.billion_state_budget_profile import build_billion_state_profiles
from jianmu.self_learning.darwinforge.billion_state_memory_guard import run_billion_state_memory_guard


def test_billion_state_allocator_uses_lazy_index_for_1b(tmp_path) -> None:
    profile = build_billion_state_profiles(["state_1B"])[0]
    guard = run_billion_state_memory_guard(tmp_path, [profile])["profiles"][0]
    allocation = allocate_billion_state_budget(profile, guard)
    assert allocation["allocated"] is True
    assert allocation["materialization_level"] == "lazy_indexed"

