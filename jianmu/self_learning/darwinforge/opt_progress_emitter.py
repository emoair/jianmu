from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO


def format_elapsed(seconds: float) -> str:
    total = max(0, int(seconds))
    hours, rem = divmod(total, 3600)
    minutes, sec = divmod(rem, 60)
    return f"{hours:02d}:{minutes:02d}:{sec:02d}"


class OptProgressEmitter:
    def __init__(self, trace_path: str | Path, stdout_capture_path: str | Path | None = None) -> None:
        self.trace_path = Path(trace_path)
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        self.stdout_capture_path = Path(stdout_capture_path) if stdout_capture_path else None
        if self.stdout_capture_path:
            self.stdout_capture_path.parent.mkdir(parents=True, exist_ok=True)
        self.lines_written = 0
        self.first_monotonic: float | None = None
        self.last_monotonic: float | None = None

    def emit(self, payload: dict, stream: TextIO | None = None) -> str:
        now = time.monotonic()
        self.first_monotonic = now if self.first_monotonic is None else self.first_monotonic
        self.last_monotonic = now
        payload = {**payload, "utc_time": datetime.now(timezone.utc).isoformat(), "progress_monotonic": now}
        line = self._format_line(payload)
        with self.trace_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
        if self.stdout_capture_path:
            with self.stdout_capture_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(line + "\n")
                handle.flush()
        print(line, flush=True, file=stream)
        self.lines_written += 1
        return line

    def timestamp_span_seconds(self) -> float:
        if self.first_monotonic is None or self.last_monotonic is None:
            return 0.0
        return self.last_monotonic - self.first_monotonic

    @staticmethod
    def _format_line(payload: dict) -> str:
        elapsed = format_elapsed(float(payload.get("actual_elapsed_seconds", 0.0)))
        cycle = payload.get("cycle", "0/0")
        phase = payload.get("phase", "backend_validation")
        ok = payload.get("compiler_verified_correctness_rate", 0.0)
        frontend_delta = payload.get("frontend_delta", 0)
        backend_delta = payload.get("backend_cl_delta", 0)
        link_delta = payload.get("backend_link_delta", 0)
        exe_delta = payload.get("backend_exe_delta", 0)
        rate = payload.get("backend_rate_per_min", payload.get("backend_rate_per_sec", 0.0))
        last_age = payload.get("last_backend_age_sec", 0.0)
        state = payload.get("active_state", "unknown")
        idle_windows = payload.get("idle_windows", 0)
        active_ratio = payload.get("active_window_ratio", 0.0)
        git_proc = payload.get("git_process_count", 0)
        return (
            f"[OPT][elapsed={elapsed}][cycle={cycle}][phase={phase}][state={state}] "
            f"frontend={payload.get('frontend_generated_events', 0)}(+{frontend_delta}) "
            f"syntax={payload.get('frontend_syntax_filtered_events', 0)} "
            f"backend_cl={payload.get('backend_cl_invocations', 0)}(+{backend_delta}) "
            f"link={payload.get('backend_link_invocations', 0)}(+{link_delta}) "
            f"exe={payload.get('backend_exe_runs', 0)}(+{exe_delta}) "
            f"rate={float(rate):.3f}/min last_backend={float(last_age):.3f}s ok={ok:.3f} "
            f"mirror={payload.get('mirror_state', 'A_active/B_frozen')} "
            f"feedback={payload.get('mirror_feedback_events', 0)} "
            f"rq_adjust={payload.get('redqueen_adjustment_events', 0)} "
            f"lane_swaps={payload.get('lane_swaps', 0)} "
            f"artifact_root={payload.get('artifact_root', '')} "
            f"git_proc={git_proc} git_guard={payload.get('git_guard', 'unknown')} "
            f"security={payload.get('security_status', 'unknown')} "
            f"rss_mb={payload.get('rss_mb', 0)} queue={payload.get('queue_status', 'normal')} "
            f"idle_windows={idle_windows} active_ratio={float(active_ratio):.3f}"
        )
