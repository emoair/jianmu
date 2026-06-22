from jianmu.self_learning.darwinforge.time_integrity_guard import build_time_integrity_guard, wall_clock_minimum_satisfied


def test_time_integrity_guard_rejects_planned_as_actual():
    result = build_time_integrity_guard()
    assert result["planned_time_rejected_as_actual"] is True


def test_time_integrity_guard_requires_actual_elapsed():
    assert wall_clock_minimum_satisfied(10, 1) is False
    assert wall_clock_minimum_satisfied(3600, 1) is True
