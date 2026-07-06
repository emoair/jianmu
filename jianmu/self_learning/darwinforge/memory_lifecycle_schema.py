from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryLifecycleRepairConfig:
    dataset_samples: int = 250_000
    backend_events: int = 40_000
    duration_minutes: int = 90
    minimum_actual_elapsed_seconds: int = 5_400
    minimum_backend_cl_invocations: int = 20_000
    minimum_backend_link_invocations: int = 20_000
    minimum_backend_exe_runs: int = 20_000
    workers: int = 16
    compiler_workers: int = 16
    progress_interval_seconds: int = 10
    memory_snapshot_interval_seconds: int = 60
    max_trace_shard_size_bytes: int = 44_000_000
    hard_fail_trace_shard_size_bytes: int = 50_000_000
    max_queue_size: int = 64
    max_preview_bytes: int = 4096
    evidence_count: int = 500
    warning_rss_percent: float = 70.0
    hard_rss_percent: float = 85.0


def memory_lifecycle_contract() -> dict:
    return {
        "version": "v1.0.8.8.5",
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
        "production_support_completed": False,
        "requires_streaming_dataset": True,
        "requires_streaming_manifest": True,
        "requires_bounded_queue": True,
        "requires_subprocess_output_streaming": True,
        "requires_memory_snapshots": True,
    }
