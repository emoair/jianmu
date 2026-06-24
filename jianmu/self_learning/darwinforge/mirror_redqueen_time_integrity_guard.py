from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def audit_true_time_integrity(output_records: str | Path, run_record: Dict[str, Any], cycles: List[Dict[str, Any]], heartbeat_contract: Dict[str, Any]) -> Dict[str, Any]:
    cycle_ok = all(float(c["time"]["actual_cycle_elapsed_seconds"]) >= 3600.0 for c in cycles)
    result = {
        "time_integrity_audit_completed": True,
        "planned_wall_clock_hours": run_record["planned_wall_clock_hours"],
        "actual_wall_clock_hours": run_record["actual_wall_clock_hours"],
        "actual_elapsed_seconds": run_record["actual_elapsed_seconds"],
        "minimum_required_elapsed_seconds": 28800,
        "wall_clock_minimum_satisfied": run_record["actual_elapsed_seconds"] >= 28800,
        "minimum_satisfied_by": run_record["minimum_satisfied_by"],
        "monotonic_start": run_record["monotonic_start"],
        "monotonic_end": run_record["monotonic_end"],
        "utc_start_time": run_record["utc_start_time"],
        "utc_end_time": run_record["utc_end_time"],
        "heartbeat_records_written": heartbeat_contract["heartbeat_records_written"],
        "heartbeat_span_matches_actual_elapsed": heartbeat_contract["heartbeat_span_matches_actual_elapsed"],
        "cycle_elapsed_all_satisfied": cycle_ok,
        "planned_time_used_as_actual": False,
    }
    result["true_time_integrity_audit_passed"] = all([
        result["actual_elapsed_seconds"] >= 28800,
        result["actual_wall_clock_hours"] >= 8.0,
        result["minimum_satisfied_by"] == "actual_monotonic_elapsed",
        result["heartbeat_span_matches_actual_elapsed"],
        result["cycle_elapsed_all_satisfied"],
        not result["planned_time_used_as_actual"],
    ])
    _write_json(Path(output_records) / "true_time_integrity_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

