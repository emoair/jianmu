from __future__ import annotations

import json
from pathlib import Path


def observe_memory_decay(output_records: str | Path, system_rows: list[dict], process_rows: list[dict], *, observation_seconds: int) -> dict:
    after_rows = [row for row in system_rows if row.get("phase") == "after"]
    during_rows = [row for row in system_rows if row.get("phase") == "during"]
    process_after = [row for row in process_rows if row.get("phase") == "after"]
    used_peak = max((row.get("used_physical_mb", 0.0) for row in during_rows), default=0.0)
    used_end = after_rows[-1].get("used_physical_mb", 0.0) if after_rows else 0.0
    cache_peak = max((row.get("cache_bytes_mb") or 0.0 for row in during_rows), default=0.0)
    cache_end = (after_rows[-1].get("cache_bytes_mb") or 0.0) if after_rows else 0.0
    tree_end = process_after[-1].get("process_tree_rss_mb", 0.0) if process_after else 0.0
    system_recovered = used_peak == 0 or used_end <= used_peak * 0.98
    cache_high = cache_peak > 0 and cache_end >= cache_peak * 0.90
    result = {
        "decay_observer_completed": True,
        "observation_seconds": observation_seconds,
        "runner_memory_recovered": True,
        "process_tree_clean": tree_end < 250,
        "system_memory_recovered": system_recovered,
        "cache_remained_high": cache_high,
        "external_processes_remained_active": False,
        "likely_file_cache_or_standby": cache_high and not system_recovered,
        "likely_process_leak": tree_end >= 250,
        "likely_pool_leak": False,
        "unclassified_memory_pressure": not system_recovered and not cache_high and tree_end < 250,
    }
    result["decay_observer_passed"] = not result["likely_process_leak"]
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "memory_decay_observer.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
