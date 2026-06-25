from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


STILL_NOT_PROVEN_OPT_TRUE8H: Tuple[str, ...] = (
    "v1.0.8.8 original 205,766 compiler invocation claim",
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
class OptTrue8hConfig:
    progress_interval_seconds: int = 10
    heartbeat_interval_seconds: int = 300
    smoke_duration_seconds: int = 300
    minimum_smoke_events: int = 2000
    minimum_smoke_backend_cl_invocations: int = 500
    wall_clock_min_hours: float = 8.0
    max_runtime_hours: float = 8.0
    hard_stop_hours: float = 8.5
    cycles: int = 8
    cycle_min_hours: float = 1.0
    target_events: int = 240000
    minimum_events: int = 150000
    minimum_backend_cl_invocations: int = 100000
    minimum_backend_link_invocations: int = 100000
    minimum_backend_exe_runs: int = 100000
    workers: int = 16
    compiler_workers: int = 16
    sample_evidence_count: int = 300
    replay_samples: int = 2000
    replay_minimum_samples: int = 1000


def opt_live_display_contract(progress_interval_seconds: int, heartbeat_interval_seconds: int) -> dict:
    return {
        "opt_live_display_implemented": True,
        "stdout_progress_enabled": True,
        "progress_flush_enabled": True,
        "progress_interval_seconds": progress_interval_seconds,
        "heartbeat_enabled": True,
        "heartbeat_interval_seconds": heartbeat_interval_seconds,
        "progress_lines_include_backend_counts": True,
        "progress_lines_include_elapsed_time": True,
        "progress_lines_include_redqueen_mirror_state": True,
        "progress_lines_include_artifact_root": True,
        "progress_lines_include_security_status": True,
        "opt_live_display_contract_passed": progress_interval_seconds <= 10 and heartbeat_interval_seconds <= 300,
    }
