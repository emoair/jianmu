from __future__ import annotations

from jianmu.self_learning.darwinforge.billion_state_budget_profile import build_billion_state_profiles
from jianmu.self_learning.darwinforge.billion_state_memory_guard import run_billion_state_memory_guard


def test_billion_state_memory_guard_blocks_unsafe_full_materialization(tmp_path) -> None:
    profile = build_billion_state_profiles(["state_1B"])[0]
    result = run_billion_state_memory_guard(tmp_path, [profile])
    row = result["profiles"][0]
    assert row["can_fully_materialize"] is False
    assert row["can_lazy_index"] is True
    assert row["recommended_materialization_level"] == "lazy_indexed"


def test_billion_state_memory_guard_preserves_100m_reference_lazy_policy(tmp_path) -> None:
    profile = build_billion_state_profiles(["state_100M_reference"])[0]
    result = run_billion_state_memory_guard(tmp_path, [profile])
    row = result["profiles"][0]
    assert row["recommended_materialization_level"] == "lazy_indexed"
