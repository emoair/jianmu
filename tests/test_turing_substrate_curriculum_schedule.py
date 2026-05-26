from __future__ import annotations

from jianmu.self_learning.darwinforge.turing_substrate_curriculum_schedule import REQUIRED_STAGES, build_turing_substrate_curriculum_schedule


def test_turing_substrate_curriculum_schedule_has_required_stages() -> None:
    schedule = build_turing_substrate_curriculum_schedule()
    names = [row["stage_name"] for row in schedule["stages"]]
    assert names == REQUIRED_STAGES
    assert all(row["promotion_allowed"] is False for row in schedule["stages"])
    assert all(row["real_promotion_allowed"] is False for row in schedule["stages"])
