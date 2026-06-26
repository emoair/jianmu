from __future__ import annotations

import json
from pathlib import Path


def detect_too_perfect_output(summary: dict, progress_rows: list[dict], *, output_records: str | Path | None = None) -> dict:
    exact_config_duration = (
        "planned_wall_clock_hours" in summary
        and "actual_wall_clock_hours" in summary
        and float(summary.get("planned_wall_clock_hours") or 0.0) == float(summary.get("actual_wall_clock_hours") or -1.0)
    )
    fixed_progress_without_work = bool(progress_rows) and all(int(row.get("backend_cl_delta", 0) or 0) == 0 for row in progress_rows)
    no_timestamp_jitter = False
    times = [float(row.get("actual_elapsed_seconds", 0.0) or 0.0) for row in progress_rows]
    if len(times) > 3:
        intervals = [round(times[i] - times[i - 1], 3) for i in range(1, len(times))]
        no_timestamp_jitter = len(set(intervals)) <= 1
    result = {
        "too_perfect_output_detector_completed": True,
        "exact_config_duration_pattern_detected": exact_config_duration,
        "fixed_progress_without_work_detected": fixed_progress_without_work,
        "counter_pattern_without_manifest_support": False,
        "summary_detail_mismatch_detected": False,
        "planned_as_actual_detected": exact_config_duration,
        "opt_trace_timestamps_lack_jitter": no_timestamp_jitter,
    }
    result["too_perfect_output_detected"] = any([
        result["exact_config_duration_pattern_detected"],
        result["fixed_progress_without_work_detected"],
        result["counter_pattern_without_manifest_support"],
        result["summary_detail_mismatch_detected"],
        result["planned_as_actual_detected"],
    ])
    result["too_perfect_output_detector_passed"] = not result["too_perfect_output_detected"]
    if output_records is not None:
        out = Path(output_records)
        out.mkdir(parents=True, exist_ok=True)
        (out / "too_perfect_output_detector.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
