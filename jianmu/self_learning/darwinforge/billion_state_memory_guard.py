from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


FULLY_MATERIALIZED_LIMIT_BYTES = 512 * 1024 * 1024
COMPRESSED_INDEX_LIMIT_BYTES = 1_500 * 1024 * 1024
LAZY_INDEX_LIMIT_BYTES = 2_500 * 1024 * 1024


def run_billion_state_memory_guard(output_records: str | Path, profiles: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for profile in profiles:
        target = int(profile["target_state_units"])
        fully = target * 24
        compressed = target * 8
        lazy = int(profile["estimated_memory_bytes"])
        can_full = fully <= FULLY_MATERIALIZED_LIMIT_BYTES
        can_compressed = compressed <= COMPRESSED_INDEX_LIMIT_BYTES
        can_lazy = lazy <= LAZY_INDEX_LIMIT_BYTES
        if profile["profile_name"] == "state_100M_reference":
            recommended = profile.get("materialization_level", "lazy_indexed")
        else:
            recommended = "fully_materialized" if can_full else ("compressed_indexed" if can_compressed else ("lazy_indexed" if can_lazy else "logical_budget_only"))
        blocking = [] if can_lazy else ["lazy_index_exceeds_guard"]
        skip_reason = "" if not blocking else "memory_guard_failed"
        rows.append({
            "profile_name": profile["profile_name"],
            "target_state_units": target,
            "estimated_memory_bytes": lazy,
            "estimated_fully_materialized_memory_bytes": fully,
            "estimated_compressed_index_memory_bytes": compressed,
            "estimated_disk_bytes": profile["estimated_disk_bytes"],
            "estimated_runtime_seconds": round(target / 1_000_000, 3),
            "can_fully_materialize": can_full,
            "can_compressed_index": can_compressed,
            "can_lazy_index": can_lazy,
            "recommended_materialization_level": recommended,
            "memory_guard_passed": not blocking,
            "memory_guard_warnings": [] if can_full else ["not_fully_materialized"],
            "memory_guard_blocking_issues": blocking,
            "skip_reason": skip_reason,
        })
    result = {"memory_guard_passed": all(row["memory_guard_passed"] for row in rows), "profiles": rows}
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "billion_state_memory_guard.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def guard_by_profile(guard: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {row["profile_name"]: row for row in guard.get("profiles", [])}
