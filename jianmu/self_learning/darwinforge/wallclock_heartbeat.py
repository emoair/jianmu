from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List

from jianmu.self_learning.darwinforge.wallclock_timer import utc_now_iso


class HeartbeatWriter:
    def __init__(self, path: str | Path, interval_seconds: int = 300, interval_events: int = 10_000) -> None:
        self.path = Path(path)
        self.interval_seconds = interval_seconds
        self.interval_events = interval_events
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records: List[Dict[str, object]] = []
        self._last_monotonic = 0.0
        self._last_events = 0

    def maybe_write(self, *, total_events: int, force: bool = False) -> None:
        now = time.monotonic()
        if force or not self.records or now - self._last_monotonic >= self.interval_seconds or total_events - self._last_events >= self.interval_events:
            row = {
                "heartbeat_index": len(self.records),
                "heartbeat_utc": utc_now_iso(),
                "heartbeat_monotonic": now,
                "total_events": total_events,
            }
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            self.records.append(row)
            self._last_monotonic = now
            self._last_events = total_events

    def contract(self, actual_elapsed_seconds: float) -> Dict[str, object]:
        span = 0.0
        if len(self.records) >= 2:
            span = float(self.records[-1]["heartbeat_monotonic"]) - float(self.records[0]["heartbeat_monotonic"])
        return {
            "heartbeat_enabled": True,
            "heartbeat_interval_seconds": self.interval_seconds,
            "heartbeat_interval_events": self.interval_events,
            "heartbeat_records_written": len(self.records),
            "first_heartbeat_utc": self.records[0]["heartbeat_utc"] if self.records else "",
            "last_heartbeat_utc": self.records[-1]["heartbeat_utc"] if self.records else "",
            "heartbeat_monotonic_span_seconds": span,
            "heartbeat_span_matches_actual_elapsed": len(self.records) > 0 and span <= actual_elapsed_seconds,
            "heartbeat_contract_passed": len(self.records) > 0 and span <= actual_elapsed_seconds,
        }
