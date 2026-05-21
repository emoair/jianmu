from __future__ import annotations

from typing import Dict, Iterable, List


DEFAULT_METRICS = [
    "global_correct_targetir_in_beam_rate",
    "candidate_space_failure_rate",
    "ood_false_accept_rate",
    "arithmetic_supported_retention_rate",
    "stable_root_count",
    "toxic_event_count",
]


def audit_parallel_equivalence(serial_metrics: Dict, parallel_metrics: Dict, acceptable_delta: float = 0.0, metric_names: Iterable[str] = None) -> Dict:
    differing: List[str] = []
    max_delta = 0.0
    for name in metric_names or DEFAULT_METRICS:
        left = serial_metrics.get(name)
        right = parallel_metrics.get(name)
        if left is None or right is None:
            continue
        delta = abs(float(left) - float(right))
        max_delta = max(max_delta, delta)
        if delta > acceptable_delta:
            differing.append(name)
    return {
        "metric_equivalence_passed": not differing,
        "differing_metric_names": differing,
        "max_abs_delta": round(max_delta, 8),
        "acceptable_delta": acceptable_delta,
        "serial_runtime_seconds": serial_metrics.get("runtime_seconds", 0.0),
        "parallel_runtime_seconds": parallel_metrics.get("runtime_seconds", 0.0),
        "speedup_ratio": round(
            float(serial_metrics.get("runtime_seconds", 0.0)) / float(parallel_metrics.get("runtime_seconds", 1.0)),
            6,
        )
        if parallel_metrics.get("runtime_seconds", 0.0)
        else 0.0,
        "nondeterminism_reason": "" if not differing else "metric_delta_exceeded",
    }

