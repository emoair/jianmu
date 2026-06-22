from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def audit_v1_0_8_6_time_claim(source_records: str | Path, observed_elapsed_minutes: float | None = 40.0) -> Dict[str, Any]:
    source = Path(source_records)
    summary_path = source / "endurance_summary.json"
    summary = _load(summary_path)
    cycle_paths = sorted((source / "cycles").glob("cycle_*/cycle_execution_metrics.json")) if (source / "cycles").exists() else []
    cycles = [_load(path) for path in cycle_paths]
    timing_keys = {"start_time", "end_time", "started_at", "completed_at", "monotonic_start", "monotonic_end", "elapsed_seconds", "actual_elapsed_seconds", "actual_wall_clock_hours"}
    actual_start_found = any(key in summary for key in ("start_time", "started_at", "utc_start_time"))
    actual_end_found = any(key in summary for key in ("end_time", "completed_at", "utc_end_time"))
    monotonic_found = "monotonic_start" in summary and "monotonic_end" in summary
    cycle_elapsed_found = all("cycle_elapsed_seconds" in cycle or "actual_elapsed_seconds" in cycle for cycle in cycles) if cycles else False
    trace_timestamp_found = any(timing_keys.intersection(cycle.keys()) for cycle in cycles)
    reconstructed_seconds = None
    if "actual_elapsed_seconds" in summary:
        reconstructed_seconds = float(summary["actual_elapsed_seconds"])
    elif observed_elapsed_minutes is not None:
        reconstructed_seconds = observed_elapsed_minutes * 60.0
    reconstructed_hours = None if reconstructed_seconds is None else reconstructed_seconds / 3600.0
    claimed_hours = summary.get("wall_clock_hours")
    has_real_timing = actual_start_found and actual_end_found and monotonic_found and cycle_elapsed_found
    if not source.exists() or not summary_path.exists():
        status = "failed"
    elif not has_real_timing:
        status = "unverified_missing_timestamps"
    elif reconstructed_hours is not None and claimed_hours is not None and abs(float(claimed_hours) - reconstructed_hours) > 0.25:
        status = "mismatch_claimed_vs_reconstructed"
    else:
        status = "verified_true_wallclock"
    planned_as_actual = bool(claimed_hours == 8.0 and not has_real_timing)
    if planned_as_actual:
        status = "planned_time_used_as_actual"
    downgraded = status != "verified_true_wallclock"
    return {
        "source_records_found": source.exists(),
        "claimed_wall_clock_hours": claimed_hours,
        "claimed_cycles_completed": summary.get("cycles_completed"),
        "claimed_total_events": summary.get("total_events"),
        "claimed_real_compiler_invocations": summary.get("real_compiler_invocations"),
        "actual_start_time_found": actual_start_found,
        "actual_end_time_found": actual_end_found,
        "monotonic_timing_found": monotonic_found,
        "cycle_elapsed_seconds_found": cycle_elapsed_found,
        "heartbeat_timestamps_found": (source / "repair_validation_heartbeat.jsonl").exists() or (source / "wallclock_heartbeat.jsonl").exists(),
        "trace_timestamp_span_found": trace_timestamp_found,
        "reconstructed_actual_elapsed_seconds": reconstructed_seconds,
        "reconstructed_actual_wall_clock_hours": reconstructed_hours,
        "observed_user_reported_elapsed_minutes": observed_elapsed_minutes,
        "claimed_vs_reconstructed_mismatch": bool(reconstructed_hours is not None and claimed_hours is not None and abs(float(claimed_hours) - reconstructed_hours) > 0.25),
        "time_claim_integrity_status": status,
        "v1_0_8_6_endurance_claim_accepted": status == "verified_true_wallclock",
        "v1_0_8_6_endurance_claim_downgraded": downgraded,
        "downgrade_reason": "" if not downgraded else "v1.0.8.6 lacks monotonic start/end, UTC start/end, cycle elapsed seconds, and heartbeat span evidence for the claimed 8h wall clock.",
        "audit_notes": "Claimed duration is not accepted without actual monotonic timing evidence.",
    }


def _load(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
