from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


SAFE_FULL_MATERIALIZATION_BYTES = 512 * 1024 * 1024


def run_state_budget_memory_guard(output_records: str | Path, profiles: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for profile in profiles:
        estimated = int(profile["estimated_memory_bytes"])
        fully_materialized_estimate = int(profile["target_state_units"] * 24)
        can_full = fully_materialized_estimate <= SAFE_FULL_MATERIALIZATION_BYTES
        requested = profile["materialization_level"]
        recommended = requested
        warnings = []
        blocking = []
        if not can_full and recommended == "fully_materialized":
            recommended = "compressed_indexed"
            warnings.append("full_materialization_exceeds_guard")
        if profile["target_state_units"] >= 100_000_000 and requested == "fully_materialized":
            blocking.append("hundred_million_cannot_be_fully_materialized_under_guard")
        rows.append({
            "profile_name": profile["profile_name"],
            "target_state_units": profile["target_state_units"],
            "estimated_memory_bytes": estimated,
            "estimated_fully_materialized_memory_bytes": fully_materialized_estimate,
            "estimated_disk_bytes": int(profile["target_state_units"] * 0.75),
            "estimated_runtime_seconds": round(profile["target_state_units"] / 1_250_000, 3),
            "can_fully_materialize": can_full,
            "recommended_materialization_level": recommended,
            "memory_guard_passed": not blocking,
            "memory_guard_warnings": warnings,
            "memory_guard_blocking_issues": blocking,
        })
    result = {"memory_guard_passed": all(row["memory_guard_passed"] for row in rows), "profiles": rows}
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "state_budget_memory_guard.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def guard_by_profile(guard: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {row["profile_name"]: row for row in guard.get("profiles", [])}
