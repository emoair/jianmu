from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WindowsMemoryAttributionConfig:
    duration_minutes: int = 30
    minimum_actual_elapsed_seconds: int = 1800
    baseline_seconds: int = 60
    post_run_observation_seconds: int = 180
    snapshot_interval_seconds: int = 5
    top_process_interval_seconds: int = 10
    dataset_samples: int = 100_000
    backend_events: int = 10_000
    workers: int = 16
    compiler_workers: int = 16
    record_top_processes: int = 20
    max_trace_shard_size_bytes: int = 44_000_000
    hard_fail_trace_shard_size_bytes: int = 50_000_000


def windows_memory_attribution_contract() -> dict:
    return {
        "version": "v1.0.8.8.6",
        "system_memory_required": True,
        "process_tree_required": True,
        "top_process_snapshot_required": True,
        "artifact_cache_required": True,
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
        "production_support_completed": False,
    }
