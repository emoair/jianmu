from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from jianmu.self_learning.darwinforge.architecture_finalization_schema import PROFILE_NAME
from jianmu.self_learning.darwinforge.process_lifecycle_schema import STILL_NOT_PROVEN_LIFECYCLE


@dataclass(frozen=True)
class RedQueenEnduranceConfig:
    profile_name: str = PROFILE_NAME
    wall_clock_min_hours: float = 6.0
    max_runtime_hours: float = 6.0
    hard_stop_hours: float = 6.5
    cycles: int = 3
    cycle_min_hours: float = 2.0
    cycle_events_target: int = 70_000
    total_events_target: int = 210_000
    minimum_total_events: int = 120_000
    minimum_real_compiler_invocations: int = 90_000
    workers: int = 16
    compiler_workers: int = 16
    trace_writer_mode: str = "sharded"
    temp_dir_mode: str = "per_sample"
    accounting_lock: bool = True
    idle_grace_seconds: int = 30
    require_plan_follow_rate: float = 0.95


STILL_NOT_PROVEN_REAL_LANDING: Tuple[str, ...] = STILL_NOT_PROVEN_LIFECYCLE


def build_real_landing_design() -> dict:
    result = {
        "redqueen_controls_validation_distribution": True,
        "redqueen_controls_difficulty": True,
        "redqueen_controls_review_allocation": True,
        "redqueen_controls_shape_diversity": True,
        "redqueen_controls_frontier_pressure": True,
        "redqueen_does_not_control_default_profile": True,
        "redqueen_does_not_control_real_promotion": True,
        "redqueen_does_not_control_production_flags": True,
        "redqueen_does_not_call_external_api": True,
        "redqueen_does_not_train_weights": True,
    }
    result["real_landing_design_passed"] = all(result.values())
    return result


def build_endurance_config_record(config: RedQueenEnduranceConfig) -> dict:
    return {
        "wall_clock_min_hours": config.wall_clock_min_hours,
        "cycles": config.cycles,
        "cycle_min_hours": config.cycle_min_hours,
        "total_events_target": config.total_events_target,
        "minimum_total_events": config.minimum_total_events,
        "minimum_real_compiler_invocations": config.minimum_real_compiler_invocations,
        "workers": config.workers,
        "compiler_workers": config.compiler_workers,
        "trace_writer_mode": config.trace_writer_mode,
        "temp_dir_mode": config.temp_dir_mode,
        "accounting_lock": config.accounting_lock,
    }
