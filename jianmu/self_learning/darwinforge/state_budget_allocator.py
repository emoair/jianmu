from __future__ import annotations

from typing import Any, Dict


def allocate_state_budget(profile: Dict[str, Any], guard_row: Dict[str, Any]) -> Dict[str, Any]:
    if not guard_row.get("memory_guard_passed", False):
        return {"allocated": False, "skipped_with_reason": "memory_guard_failed", "actual_state_units_allocated": 0, "peak_memory_bytes": 0, "disk_bytes_written": 0}
    materialization = guard_row.get("recommended_materialization_level", profile["materialization_level"])
    peak_factor = {"fully_materialized": 0.90, "compressed_indexed": 0.55, "lazy_indexed": 0.18, "logical_budget_only": 0.05, "simulated_budget": 0.02}[materialization]
    return {
        "allocated": True,
        "skipped_with_reason": "",
        "actual_state_units_allocated": profile["actual_state_units_allocated"],
        "materialization_level": materialization,
        "peak_memory_bytes": int(profile["estimated_memory_bytes"] * peak_factor),
        "disk_bytes_written": int(profile["target_state_units"] * (0.35 if materialization != "fully_materialized" else 0.8)),
    }

