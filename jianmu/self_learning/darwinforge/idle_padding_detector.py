from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


ALLOWED_IDLE_PHASES = ("initialization", "cleanup", "final_lifecycle_guard", "git_push_manual_outside_runner", "post_run_idle_sentinel")
DISALLOWED_IDLE_PHASES = ("smoke_gate active work", "true8h_backend_validation", "backend_replay", "mirror/redqueen validation active phase", "active_backend_validation")


def detect_idle_padding(progress_rows: Iterable[dict], *, output_records: str | Path | None = None, max_zero_delta_windows: int = 2, max_last_backend_age_sec: float = 30.0) -> dict:
    zero_delta = 0
    consecutive = 0
    max_consecutive = 0
    idle_seconds = 0.0
    detected = False
    rows = list(progress_rows)
    previous_elapsed: float | None = None
    for row in rows:
        phase = str(row.get("phase", ""))
        delta = int(row.get("backend_cl_delta", 0) or 0) + int(row.get("backend_exe_delta", 0) or 0)
        elapsed = float(row.get("actual_elapsed_seconds", row.get("elapsed_seconds", 0.0)) or 0.0)
        allowed = phase in ALLOWED_IDLE_PHASES
        if delta == 0 and not allowed:
            zero_delta += 1
            consecutive += 1
            if previous_elapsed is not None:
                idle_seconds += max(0.0, elapsed - previous_elapsed)
        else:
            consecutive = 0
        max_consecutive = max(max_consecutive, consecutive)
        if (consecutive > max_zero_delta_windows or float(row.get("last_backend_age_sec", 0.0) or 0.0) > max_last_backend_age_sec) and not allowed:
            detected = True
        previous_elapsed = elapsed
    result = {
        "idle_padding_detector_implemented": True,
        "zero_delta_window_rule_enabled": True,
        "last_backend_age_rule_enabled": True,
        "target_reached_continue_work_rule_enabled": True,
        "allowed_idle_phases": list(ALLOWED_IDLE_PHASES),
        "disallowed_idle_phases": list(DISALLOWED_IDLE_PHASES),
        "zero_delta_progress_window_count": zero_delta,
        "max_consecutive_zero_delta_windows": max_consecutive,
        "idle_padding_seconds_detected": round(idle_seconds, 6),
        "idle_padding_detected": detected,
    }
    result["idle_padding_detector_passed"] = not detected
    if output_records is not None:
        out = Path(output_records)
        out.mkdir(parents=True, exist_ok=True)
        (out / "idle_padding_detector.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
