from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


TIME_REPAIR_STILL_NOT_PROVEN: Tuple[str, ...] = (
    "v1.0.8.6 true 8-hour validation, unless verified by audit",
    "production function support completed",
    "production array support completed",
    "production recursion support completed",
    "RedQueen autonomous governance completed",
    "production readiness",
    "formal Turing completeness proof",
    "solved program synthesis",
    "natural language layer completed",
)


@dataclass(frozen=True)
class TimeRepairValidationConfig:
    planned_wall_clock_hours: float = 2.0
    max_runtime_hours: float = 2.0
    hard_stop_hours: float = 2.25
    cycles: int = 2
    planned_cycle_min_hours: float = 1.0
    target_events: int = 70_000
    minimum_events: int = 40_000
    minimum_real_compiler_invocations: int = 25_000
    heartbeat_interval_seconds: int = 300
    heartbeat_interval_events: int = 10_000
    idle_grace_seconds: int = 30
    workers: int = 16
    compiler_workers: int = 16
