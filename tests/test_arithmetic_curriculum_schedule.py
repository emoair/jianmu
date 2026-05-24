from jianmu.self_learning.darwinforge.arithmetic_curriculum_schedule import REQUIRED_STAGES, build_arithmetic_curriculum_schedule


def test_curriculum_schedule_has_required_stages():
    schedule = build_arithmetic_curriculum_schedule()
    assert [row["stage_name"] for row in schedule["stages"]] == REQUIRED_STAGES
    assert all(row["real_promotion_allowed"] is False for row in schedule["stages"])
