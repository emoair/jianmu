from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class SampleProcessingCounters:
    mode: str
    seed: int = 42
    reported_train_count: int = 0
    actual_train_iterated_count: int = 0
    reported_eval_count: int = 0
    actual_eval_iterated_count: int = 0
    reported_external_ood_count: int = 0
    actual_external_ood_iterated_count: int = 0
    freebeam_eval_call_count: int = 0
    compiler_eval_call_count: int | str = "unavailable"
    canonicalizer_call_count: int = 0
    branchchain_route_call_count: int = 0
    root_colony_update_call_count: int = 0
    runtime_capture_event_count: int = 0
    baseline_eval_call_count: int = 0
    ablation_eval_call_count: int = 0
    cross_process_eval_call_count: int = 0
    notes: list[str] = field(default_factory=list)

    def increment_phase(self, phase: str, count: int = 1) -> None:
        if phase == "train":
            self.actual_train_iterated_count += count
        elif phase == "eval":
            self.actual_eval_iterated_count += count
            self.freebeam_eval_call_count += count
        elif phase == "external_ood":
            self.actual_external_ood_iterated_count += count
            self.freebeam_eval_call_count += count
        elif phase == "baseline":
            self.baseline_eval_call_count += count
        elif phase == "ablation":
            self.ablation_eval_call_count += count
        elif phase == "cross_process":
            self.cross_process_eval_call_count += count

    def to_dict(self) -> Dict[str, Any]:
        count_match = (
            self.reported_train_count == self.actual_train_iterated_count
            and self.reported_eval_count == self.actual_eval_iterated_count
            and self.reported_external_ood_count == self.actual_external_ood_iterated_count
        )
        suspicious_zero = any(
            [
                self.reported_train_count > 0 and self.actual_train_iterated_count == 0,
                self.reported_eval_count > 0 and self.actual_eval_iterated_count == 0,
                self.reported_external_ood_count > 0 and self.actual_external_ood_iterated_count == 0,
            ]
        )
        return {
            **self.__dict__,
            "count_match_passed": count_match,
            "suspicious_zero_loop_detected": suspicious_zero,
            "synthetic_summary_detected": suspicious_zero or not count_match,
            "blocking_issue": suspicious_zero,
        }


def counters_from_reported_metrics(mode: str, metrics: Dict[str, Any]) -> Dict[str, Any]:
    counters = SampleProcessingCounters(
        mode=mode,
        reported_train_count=int(metrics.get("train_sample_count", 0)),
        reported_eval_count=int(metrics.get("eval_sample_count", 0)),
        reported_external_ood_count=int(metrics.get("external_ood_sample_count", 0)),
        notes=["No per-sample iteration counters were present in v0.9.1 records; treated as summary-only evidence."],
    )
    return counters.to_dict()
