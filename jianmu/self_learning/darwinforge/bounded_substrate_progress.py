from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, TextIO


@dataclass
class ProgressReporter:
    enabled: bool = True
    interval_seconds: float = 2.0
    stream: TextIO = sys.stderr
    started_at: float = field(default_factory=time.perf_counter)
    last_emit_at: float = 0.0
    events_emitted: int = 0
    errors: list[str] = field(default_factory=list)

    @property
    def tty_detected(self) -> bool:
        return bool(getattr(self.stream, "isatty", lambda: False)())

    @property
    def backend(self) -> str:
        if not self.enabled:
            return "disabled"
        return "tty_bar" if self.tty_detected else "periodic_text"

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
        if not force and self.last_emit_at and now - self.last_emit_at < self.interval_seconds:
            return
        self.last_emit_at = now
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
            "elapsed": round(elapsed, 2),
            "eta": round(eta, 2),
            "samples_per_second": round(rate, 4),
        }
        fields.update(metrics or {})
        try:
            if self.tty_detected:
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
        except Exception as exc:  # progress must never hide runner failures
            self.errors.append(f"{type(exc).__name__}:{str(exc)[-120:]}")

    def summary(self) -> Dict[str, Any]:
        return {
            "progress_enabled": self.enabled,
            "progress_backend": self.backend,
            "tty_detected": self.tty_detected,
            "progress_interval_seconds": self.interval_seconds,
            "progress_events_emitted": self.events_emitted,
            "progress_errors": list(self.errors),
            "metrics_affected_by_progress": False,
        }

