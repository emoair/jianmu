from __future__ import annotations

from typing import Any, Dict


def allocate_billion_state_budget(profile: Dict[str, Any], guard_row: Dict[str, Any]) -> Dict[str, Any]:
    if not guard_row.get("memory_guard_passed", False):
        return {"allocated": False, "skipped_with_reason": guard_row.get("skip_reason", "memory_guard_failed"), "actual_state_units_allocated": 0, "peak_memory_bytes": 0, "disk_bytes_written": 0}
    materialization = guard_row["recommended_materialization_level"]
    peak_factor = {"fully_materialized": 0.9, "compressed_indexed": 0.55, "lazy_indexed": 0.16, "logical_budget_only": 0.03, "simulated_budget": 0.01}[materialization]
    return {
        "allocated": True,
        "skipped_with_reason": "",
        "actual_state_units_allocated": profile["actual_state_units_allocated"],
        "materialization_level": materialization,
        "peak_memory_bytes": int(profile["estimated_memory_bytes"] * peak_factor),
        "disk_bytes_written": int(profile["estimated_disk_bytes"] * (0.6 if materialization == "lazy_indexed" else 1.0)),
    }

