from __future__ import annotations

from typing import Dict

from jianmu.self_learning.darwinforge.controlled_opt_in_longhaul_schema import ControlledOptInLonghaulConfig


def build_longhaul_schedule(config: ControlledOptInLonghaulConfig, targets: Dict[str, int]) -> Dict[str, object]:
    return {
        "wall_clock_min_hours": config.wall_clock_min_hours,
        "max_runtime_hours": config.max_runtime_hours,
        "hard_stop_hours": config.hard_stop_hours,
        "workers": config.workers,
        "compiler_workers": config.compiler_workers,
        "targets": targets,
        "requires_8h_config": config.wall_clock_min_hours >= 8 and config.max_runtime_hours >= 8,
    }
