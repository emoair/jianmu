from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class RuntimeProfiler:
    sections: Dict[str, float] = field(default_factory=dict)
    total_started: float = field(default_factory=time.time)

    @contextmanager
    def section(self, name: str):
        started = time.time()
        try:
            yield
        finally:
            self.sections[name] = self.sections.get(name, 0.0) + (time.time() - started)

    def report(self, sample_count: int = 0, candidate_count: int = 0, serial_runtime_seconds: float = 0.0) -> Dict:
        total = time.time() - self.total_started
        speedup = serial_runtime_seconds / total if serial_runtime_seconds and total else 1.0
        return {
            "total_runtime_seconds": round(total, 6),
            "sample_eval_time_seconds": round(self.sections.get("sample_eval", 0.0), 6),
            "candidate_generation_time_seconds": round(self.sections.get("candidate_generation", 0.0), 6),
            "scoring_time_seconds": round(self.sections.get("scoring", 0.0), 6),
            "root_lifecycle_time_seconds": round(self.sections.get("root_lifecycle", 0.0), 6),
            "toxic_nutrient_time_seconds": round(self.sections.get("toxic_nutrient", 0.0), 6),
            "ood_audit_time_seconds": round(self.sections.get("ood_audit", 0.0), 6),
            "record_write_time_seconds": round(self.sections.get("record_write", 0.0), 6),
            "record_merge_time_seconds": round(self.sections.get("record_merge", 0.0), 6),
            "compiler_sandbox_time_seconds": round(self.sections.get("compiler_sandbox", 0.0), 6),
            "idle_or_wait_time_seconds": round(self.sections.get("idle_or_wait", 0.0), 6),
            "samples_per_second": round(sample_count / total, 6) if total else float(sample_count),
            "candidates_per_second": round(candidate_count / total, 6) if total else float(candidate_count),
            "compile_jobs_per_second": 0.0,
            "speedup_vs_serial": round(speedup, 6),
            "runtime_per_100_samples": round(total / max(sample_count / 100.0, 1.0), 6),
            "estimated_cpu_utilization_note": "not_measured",
        }

