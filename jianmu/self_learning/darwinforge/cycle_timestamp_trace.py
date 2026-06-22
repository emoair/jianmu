from __future__ import annotations

from typing import Dict

from jianmu.self_learning.darwinforge.wallclock_timer import WallClockTimer


def build_cycle_timestamp_record(cycle_index: int, planned_cycle_min_hours: float, timer: WallClockTimer) -> Dict[str, object]:
    elapsed = timer.actual_elapsed_seconds
    return {
        "cycle_index": cycle_index,
        "planned_cycle_min_hours": planned_cycle_min_hours,
        "actual_cycle_wall_clock_hours": elapsed / 3600.0,
        "cycle_elapsed_seconds": elapsed,
        "cycle_monotonic_start": timer.monotonic_start,
        "cycle_monotonic_end": timer.monotonic_end,
        "cycle_utc_start_time": timer.utc_start_time,
        "cycle_utc_end_time": timer.utc_end_time,
        "cycle_minimum_satisfied_by": "actual_monotonic_elapsed",
    }
