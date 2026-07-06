from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from jianmu.self_learning.darwinforge.system_commit_cache_pool_sampler import sample_commit_cache_pool


def sample_windows_system_memory() -> dict:
    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "monotonic": time.monotonic(),
        **sample_commit_cache_pool(),
    }
    used_percent = (row["used_physical_mb"] / row["total_physical_mb"] * 100.0) if row["total_physical_mb"] else 0.0
    if used_percent >= 90 or row["commit_used_percent"] >= 90:
        pressure = "high"
    elif used_percent >= 75 or row["commit_used_percent"] >= 75:
        pressure = "medium"
    else:
        pressure = "low"
    row["system_memory_pressure_level"] = pressure
    return row


def write_system_memory_sampler_contract(output_records: str | Path, sample: dict | None = None) -> dict:
    sample = sample or sample_windows_system_memory()
    result = {
        **sample,
        "system_memory_sampler_implemented": True,
        "physical_memory_recorded": sample.get("total_physical_mb", 0) > 0,
        "commit_recorded": sample.get("commit_limit_mb", 0) > 0,
        "cache_recorded": sample.get("cache_bytes_mb") is not None,
        "pool_recorded": sample.get("paged_pool_mb") is not None and sample.get("nonpaged_pool_mb") is not None,
        "compression_recorded_or_not_available": True,
    }
    result["system_memory_sampler_passed"] = result["physical_memory_recorded"] and result["commit_recorded"] and result["cache_recorded"] and result["pool_recorded"]
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "system_memory_sampler.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
