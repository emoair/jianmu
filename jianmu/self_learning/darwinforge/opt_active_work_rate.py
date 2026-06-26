from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class ActiveWorkRateTracker:
    last_elapsed_seconds: float = 0.0
    last_frontend_total: int = 0
    last_backend_cl_total: int = 0
    last_backend_link_total: int = 0
    last_backend_exe_total: int = 0
    last_backend_monotonic: float | None = None
    active_windows: int = 0
    idle_windows: int = 0

    def payload(self, *, elapsed_seconds: float, frontend_total: int, backend_cl_total: int, backend_link_total: int, backend_exe_total: int) -> dict:
        interval = max(0.001, elapsed_seconds - self.last_elapsed_seconds)
        frontend_delta = max(0, frontend_total - self.last_frontend_total)
        cl_delta = max(0, backend_cl_total - self.last_backend_cl_total)
        link_delta = max(0, backend_link_total - self.last_backend_link_total)
        exe_delta = max(0, backend_exe_total - self.last_backend_exe_total)
        if cl_delta > 0 or exe_delta > 0:
            self.last_backend_monotonic = time.monotonic()
            self.active_windows += 1
            state = "active_backend"
        else:
            self.idle_windows += 1
            state = "idle_backend"
        total_windows = self.active_windows + self.idle_windows
        last_age = 0.0 if self.last_backend_monotonic is None else max(0.0, time.monotonic() - self.last_backend_monotonic)
        result = {
            "frontend_delta": frontend_delta,
            "backend_cl_delta": cl_delta,
            "backend_link_delta": link_delta,
            "backend_exe_delta": exe_delta,
            "backend_rate_per_sec": cl_delta / interval,
            "backend_rate_per_min": cl_delta * 60.0 / interval,
            "last_backend_age_sec": last_age,
            "active_state": state,
            "idle_windows": self.idle_windows,
            "active_window_ratio": self.active_windows / total_windows if total_windows else 0.0,
        }
        self.last_elapsed_seconds = elapsed_seconds
        self.last_frontend_total = frontend_total
        self.last_backend_cl_total = backend_cl_total
        self.last_backend_link_total = backend_link_total
        self.last_backend_exe_total = backend_exe_total
        return result
