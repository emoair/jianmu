from jianmu.self_learning.darwinforge.cycle_timestamp_trace import build_cycle_timestamp_record
from jianmu.self_learning.darwinforge.wallclock_timer import WallClockTimer


def test_cycle_timestamp_trace_records_elapsed():
    timer = WallClockTimer(0.0).start().stop()
    result = build_cycle_timestamp_record(0, 1.0, timer)
    assert result["cycle_index"] == 0
    assert "cycle_elapsed_seconds" in result
