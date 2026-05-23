from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class RealLongrunProfiler:
    started_wall: float = field(default_factory=time.perf_counter)
    started_cpu: float = field(default_factory=time.process_time)
    mode_runtime_seconds: Dict[str, float] = field(default_factory=dict)
    seed_runtime_seconds: Dict[str, float] = field(default_factory=dict)
    serialization_time_seconds: float = 0.0
    reload_time_seconds: float = 0.0
    cross_process_eval_time_seconds: float = 0.0
    baseline_runtime_seconds: float = 0.0
    ablation_runtime_seconds: float = 0.0
    records_write_time_seconds: float = 0.0
    checkpoint_count: int = 0

    def to_dict(self, total_eval_samples: int = 0, total_external_samples: int = 0) -> Dict[str, Any]:
        total_wall = max(time.perf_counter() - self.started_wall, 0.0)
        total_cpu = max(time.process_time() - self.started_cpu, 0.0)
        total_samples = total_eval_samples + total_external_samples
        return {
            "total_wall_clock_seconds": round(total_wall, 6),
            "total_cpu_seconds": round(total_cpu, 6),
            "mode_runtime_seconds": self.mode_runtime_seconds,
            "seed_runtime_seconds": self.seed_runtime_seconds,
            "samples_per_second": round(total_samples / total_wall, 6) if total_wall > 0 else 0.0,
            "eval_samples_per_second": round(total_eval_samples / total_wall, 6) if total_wall > 0 else 0.0,
            "external_ood_samples_per_second": round(total_external_samples / total_wall, 6) if total_wall > 0 else 0.0,
            "serialization_time_seconds": round(self.serialization_time_seconds, 6),
            "reload_time_seconds": round(self.reload_time_seconds, 6),
            "cross_process_eval_time_seconds": round(self.cross_process_eval_time_seconds, 6),
            "baseline_runtime_seconds": round(self.baseline_runtime_seconds, 6),
            "ablation_runtime_seconds": round(self.ablation_runtime_seconds, 6),
            "records_write_time_seconds": round(self.records_write_time_seconds, 6),
            "checkpoint_count": self.checkpoint_count,
            "peak_memory_mb": "unavailable",
            "runtime_plausibility_passed": total_wall > 0 and total_samples > 0,
            "runtime_anomaly_detected": not (total_wall > 0 and total_samples > 0),
            "anomaly_reason": "" if total_wall > 0 and total_samples > 0 else "no measurable wall-clock workload",
        }


def aggregate_mode_runtime(rows: List[Dict[str, Any]]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for row in rows:
        out[row["mode"]] = round(float(row.get("wall_clock_runtime_seconds", 0.0)), 6)
    return out
