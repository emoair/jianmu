from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, TextIO


@dataclass
class ProgressReporter:
    enabled: bool = True
    interval_seconds: float = 2.0
    min_samples: int = 100
    force_text: bool = False
    stream: TextIO = sys.stderr
    started_at: float = field(default_factory=time.perf_counter)
    last_emit_at: float = 0.0
    last_emit_processed: int = 0
    last_emit_processed_by_phase: Dict[str, int] = field(default_factory=dict)
    events_emitted: int = 0
    events_by_phase: Dict[str, int] = field(default_factory=dict)
    first_event_time: float | None = None
    last_event_time: float | None = None
    errors: list[str] = field(default_factory=list)

    @property
    def tty_detected(self) -> bool:
        return bool(getattr(self.stream, "isatty", lambda: False)())

    @property
    def backend(self) -> str:
        if not self.enabled:
            return "disabled"
        return "periodic_text" if self.force_text or not self.tty_detected else "tty_bar"

    def update(
        self,
        *,
        mode: str,
        phase: str,
        stage: str = "",
        processed: int = 0,
        total: int = 0,
        force: bool = False,
        metrics: Dict[str, Any] | None = None,
    ) -> None:
        if not self.enabled:
            return
        now = time.perf_counter()
        previous_for_phase = self.last_emit_processed_by_phase.get(phase, 0)
        sample_delta = abs(processed - previous_for_phase)
        time_ready = not self.last_emit_at or now - self.last_emit_at >= self.interval_seconds
        sample_ready = sample_delta >= max(1, self.min_samples)
        if not force and not time_ready and not sample_ready:
            return
        self.last_emit_at = now
        self.last_emit_processed = processed
        self.last_emit_processed_by_phase[phase] = processed
        elapsed = max(now - self.started_at, 1e-9)
        rate = processed / elapsed if processed else 0.0
        remaining = max(total - processed, 0)
        eta = remaining / rate if rate > 0 else 0.0
        percent = (processed / total * 100.0) if total else 0.0
        fields = {
            "mode": mode,
            "phase": phase,
            "stage": stage,
            "processed": processed,
            "total": total,
            "percent": round(percent, 2),
            "elapsed_seconds": round(elapsed, 2),
            "eta_seconds": round(eta, 2),
            "samples_per_second": round(rate, 4),
        }
        fields.update(metrics or {})
        try:
            if self.backend == "tty_bar":
                line = (
                    f"\r[{phase}] mode={mode} stage={stage or '-'} "
                    f"{processed}/{total} {percent:5.1f}% rate={rate:.2f}/s eta={eta:.1f}s"
                )
                self.stream.write(line)
                if processed >= total and total:
                    self.stream.write("\n")
            else:
                parts = " ".join(f"{key}={value}" for key, value in fields.items())
                self.stream.write(f"[progress] {parts}\n")
            self.stream.flush()
            self.events_emitted += 1
            self.events_by_phase[phase] = self.events_by_phase.get(phase, 0) + 1
            rel_time = round(now - self.started_at, 6)
            if self.first_event_time is None:
                self.first_event_time = rel_time
            self.last_event_time = rel_time
        except Exception as exc:  # progress must never hide runner failures
            self.errors.append(f"{type(exc).__name__}:{str(exc)[-120:]}")

    def summary(self) -> Dict[str, Any]:
        return {
            "progress_enabled": self.enabled,
            "progress_backend": self.backend,
            "tty_detected": self.tty_detected,
            "force_text": self.force_text,
            "progress_interval_seconds": self.interval_seconds,
            "progress_min_samples": self.min_samples,
            "progress_events_emitted": self.events_emitted,
            "progress_events_by_phase": dict(self.events_by_phase),
            "progress_first_event_time": self.first_event_time,
            "progress_last_event_time": self.last_event_time,
            "progress_errors": list(self.errors),
            "progress_overhead_estimated": "low",
            "metrics_affected_by_progress": False,
        }
