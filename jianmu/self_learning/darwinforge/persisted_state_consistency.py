from __future__ import annotations

from typing import Dict, Iterable


TRACKED_METRICS = [
    "current_supported_retention_rate",
    "overall_ood_false_accept_rate",
    "hard_ood_rejection_rate",
    "true_false_accept_trap_rejection_rate",
    "future_domain_isolation_rate",
    "near_ood_quarantine_rate",
]


def check_persisted_state_consistency(original_metrics: Dict, reloaded_metrics: Dict, allowed_delta: float = 0.02) -> Dict:
    deltas = {}
    degraded = []
    improved = []
    for name in TRACKED_METRICS:
        old = float(original_metrics.get(name, 0.0))
        new = float(reloaded_metrics.get(name, 0.0))
        delta = round(new - old, 6)
        deltas[name] = delta
        if delta < -allowed_delta:
            degraded.append(name)
        if delta > allowed_delta:
            improved.append(name)
    max_abs = max((abs(v) for v in deltas.values()), default=0.0)
    ood_delta = abs(deltas.get("overall_ood_false_accept_rate", 0.0))
    pass_conditions = (
        abs(deltas.get("current_supported_retention_rate", 0.0)) <= allowed_delta
        and ood_delta <= 0.05
        and reloaded_metrics.get("no_label_inference_passed") is True
        and reloaded_metrics.get("forbidden_field_access_count", 0) == 0
        and reloaded_metrics.get("over_rejection_detected") is False
    )
    return {
        "persisted_state_consistency_passed": pass_conditions,
        "metric_delta_summary": deltas,
        "max_abs_metric_delta": round(max_abs, 6),
        "allowed_delta": allowed_delta,
        "degraded_metrics": degraded,
        "improved_metrics": improved,
        "consistency_failure_reason": _failure_reason(pass_conditions, reloaded_metrics, degraded),
    }


def summarize_metrics_for_consistency(eval_result: Dict) -> Dict:
    metrics = dict(eval_result.get("metrics", {}))
    for key in ["no_label_inference_passed", "forbidden_field_access_count", "over_rejection_detected"]:
        metrics[key] = eval_result.get(key)
    return metrics


def _failure_reason(passed: bool, reloaded_metrics: Dict, degraded: Iterable[str]) -> str | None:
    if passed:
        return None
    if reloaded_metrics.get("no_label_inference_passed") is not True:
        return "no_label_inference_failed"
    if reloaded_metrics.get("forbidden_field_access_count", 0):
        return "forbidden_field_access"
    if reloaded_metrics.get("over_rejection_detected"):
        return "over_rejection_detected"
    if list(degraded):
        return "metric_degraded"
    return "metric_delta_too_large"
