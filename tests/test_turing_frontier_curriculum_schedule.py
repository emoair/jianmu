from __future__ import annotations

from jianmu.self_learning.darwinforge.turing_frontier_curriculum_schedule import build_frontier_schedule


def test_frontier_curriculum_schedule_has_required_stages() -> None:
    names = [row["stage_name"] for row in build_frontier_schedule()["stages"]]
    assert "future_recursion" in names
    assert "bounded_control_hard_supported" in names

