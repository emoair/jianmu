from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from jianmu.self_learning.darwinforge.redqueen_weak_signal_schema import STILL_NOT_PROVEN_WEAK_SIGNAL


STILL_NOT_PROVEN_STABILITY: Tuple[str, ...] = tuple(dict.fromkeys(STILL_NOT_PROVEN_WEAK_SIGNAL))


@dataclass(frozen=True)
class RedQueenStabilityConfig:
    profile_name: str = "staged_opt_in_function_array_recursion_v1_0_7"
    wall_clock_min_hours: float = 8.0
    max_runtime_hours: float = 8.0
    hard_stop_hours: float = 8.5
    cycles: int = 8
    cycle_min_hours: float = 1.0
    total_events_target: int = 300_000
    minimum_total_events: int = 180_000
    minimum_real_compiler_invocations: int = 130_000
    workers: int = 16
    compiler_workers: int = 16
    trace_writer_mode: str = "sharded"
    temp_dir_mode: str = "per_sample"
    accounting_lock: bool = True
    idle_grace_seconds: int = 30
    require_plan_follow_rate: float = 0.95
    require_msvc_env: bool = True


def build_multiround_stability_config_record(config: RedQueenStabilityConfig) -> Dict[str, Any]:
    return {
        "wall_clock_min_hours": config.wall_clock_min_hours,
        "cycles": config.cycles,
        "total_events_target": config.total_events_target,
        "minimum_total_events": config.minimum_total_events,
        "minimum_real_compiler_invocations": config.minimum_real_compiler_invocations,
        "workers": config.workers,
        "compiler_workers": config.compiler_workers,
        "trace_writer_mode": config.trace_writer_mode,
        "temp_dir_mode": config.temp_dir_mode,
        "accounting_lock": config.accounting_lock,
        "msvc_preflight_required": config.require_msvc_env,
        "weak_signal_schedule": {
            "cycle_0": [],
            "cycle_1": ["function_call_weak_signal"],
            "cycle_2": ["function_call_weak_signal", "mixed_integration_weak_signal"],
            "cycle_3": ["mixed_integration_weak_signal"],
            "cycle_4": [],
            "cycle_5": ["structured_recursion_stable_signal"],
            "cycle_6": ["function_call_weak_signal", "mixed_integration_weak_signal"],
            "cycle_7": [],
        },
    }
