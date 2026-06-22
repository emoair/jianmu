import time

from jianmu.self_learning.darwinforge.wallclock_timer import WallClockTimer


def test_wallclock_timer_uses_monotonic():
    timer = WallClockTimer(0.0).start()
    time.sleep(0.01)
    timer.stop()
    record = timer.record()
    assert record["actual_elapsed_seconds"] > 0
    assert record["minimum_satisfied_by"] == "actual_monotonic_elapsed"


def test_wallclock_timer_separates_planned_and_actual():
    timer = WallClockTimer(5.0).start().stop()
    record = timer.record()
    assert record["planned_wall_clock_hours"] == 5.0
    assert record["planned_duration_used_as_actual"] is False
