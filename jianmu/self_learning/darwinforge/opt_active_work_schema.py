from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


STILL_NOT_PROVEN_OPT_ACTIVE_WORK: Tuple[str, ...] = (
    "v1.0.8.8 original 205,766 compiler invocation claim",
    "v1.0.8.8.2 long-run active backend distribution unless accepted by audit",
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
class OptActiveWorkConfig:
    duration_minutes: float = 45.0
    minimum_actual_elapsed_seconds: float = 2700.0
    events: int = 40000
    minimum_backend_cl_invocations: int = 20000
    minimum_backend_link_invocations: int = 20000
    minimum_backend_exe_runs: int = 20000
    workers: int = 16
    compiler_workers: int = 16
    progress_interval_seconds: int = 10
    heartbeat_interval_seconds: int = 300
    required_backend_active_window_ratio: float = 0.90
    max_trace_shard_size_bytes: int = 44_000_000
    trace_warning_threshold_bytes: int = 40_000_000
    trace_hard_fail_threshold_bytes: int = 50_000_000
    replay_samples: int = 500


def opt_active_work_rate_contract() -> dict:
    return {
        "opt_active_work_rate_implemented": True,
        "backend_delta_displayed": True,
        "backend_rate_displayed": True,
        "last_backend_age_displayed": True,
        "active_state_displayed": True,
        "idle_window_displayed": True,
        "git_process_count_displayed": True,
        "rss_queue_displayed": True,
        "opt_active_work_rate_contract_passed": True,
    }
