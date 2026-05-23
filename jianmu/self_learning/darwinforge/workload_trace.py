from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List


TRACE_PHASES = {
    "dataset_load",
    "train_iteration",
    "eval_iteration",
    "external_ood_iteration",
    "runtime_capture",
    "state_serialization",
    "same_process_reload",
    "cross_process_spawn",
    "cross_process_load",
    "cross_process_eval",
    "baseline_eval",
    "ablation_eval",
    "comparison_pack",
    "checkpoint_flush",
    "graceful_stop",
}


@dataclass
class WorkloadTraceRecorder:
    mode: str = "audit"
    seed: int = 42
    events: List[Dict[str, Any]] = field(default_factory=list)
    cumulative_sample_count: int = 0

    def record(
        self,
        phase: str,
        function_name: str,
        sample_count_delta: int = 0,
        sample_id: str | None = None,
        batch_index: int | None = None,
        real_execution: bool = True,
        synthetic_or_summary_path: bool = False,
        notes: str = "",
    ) -> Dict[str, Any]:
        if phase not in TRACE_PHASES:
            raise ValueError(f"unknown trace phase: {phase}")
        self.cumulative_sample_count += int(sample_count_delta)
        event = {
            "timestamp": time.time(),
            "monotonic_time": time.perf_counter(),
            "mode": self.mode,
            "seed": self.seed,
            "phase": phase,
            "sample_index": batch_index,
            "sample_id_hash": _hash_sample_id(sample_id) if sample_id is not None else None,
            "batch_index": batch_index,
            "sample_count_delta": int(sample_count_delta),
            "cumulative_sample_count": self.cumulative_sample_count,
            "function_name": function_name,
            "real_execution": bool(real_execution),
            "synthetic_or_summary_path": bool(synthetic_or_summary_path),
            "notes": notes,
        }
        self.events.append(event)
        return event

    def extend(self, events: Iterable[Dict[str, Any]]) -> None:
        for event in events:
            self.events.append(dict(event))

    def write_jsonl(self, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n" for event in self.events), encoding="utf-8")


def read_workload_trace(path: str | Path) -> List[Dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def summarize_workload_trace(events: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    events = list(events)
    real = [event for event in events if event.get("real_execution")]
    summary = [event for event in events if event.get("synthetic_or_summary_path")]
    return {
        "event_count": len(events),
        "real_execution_event_count": len(real),
        "synthetic_summary_event_count": len(summary),
        "sample_count_total": sum(int(event.get("sample_count_delta", 0)) for event in events),
        "phases_seen": sorted({event.get("phase") for event in events}),
        "workload_trace_passed": bool(events) and bool(real),
    }


def _hash_sample_id(sample_id: str) -> str:
    return hashlib.sha256(sample_id.encode("utf-8")).hexdigest()[:16]
