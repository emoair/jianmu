from __future__ import annotations

from typing import Dict, List


TRACKED = [
    "current_supported_retention_rate",
    "overall_ood_false_accept_rate",
    "hard_ood_rejection_rate",
    "true_false_accept_trap_rejection_rate",
    "future_domain_isolation_rate",
    "near_ood_quarantine_rate",
]


def check_full_state_consistency(
    v087_metrics: Dict,
    v088_metrics: Dict,
    same_process: Dict,
    cross_process: Dict,
    external_ood: Dict,
    multiseed: Dict,
    forbidden_scan: Dict,
    support_level: str,
    allowed_delta: float = 0.02,
) -> Dict:
    same_metrics = same_process.get("metrics", same_process)
    base_metrics = v087_metrics or v088_metrics
    deltas = {}
    degraded: List[str] = []
    improved: List[str] = []
    for name in TRACKED:
        old = float(base_metrics.get(name, 0.0))
        new = float(same_metrics.get(name, 0.0))
        delta = round(new - old, 6)
        deltas[name] = delta
        if delta < -allowed_delta:
            degraded.append(name)
        if delta > allowed_delta:
            improved.append(name)
    max_abs = max((abs(v) for v in deltas.values()), default=0.0)
    passed = (
        support_level == "full_router_root"
        and same_process.get("no_label_inference_passed") is True
        and cross_process.get("cross_process_reload_passed") is True
        and forbidden_scan.get("forbidden_field_in_state_count", 1) == 0
        and external_ood.get("overall_ood_false_accept_rate", 1.0) <= 0.10
        and multiseed.get("stable_across_seeds") is True
        and same_process.get("current_supported_retention_rate", 0.0) >= 0.98
        and same_process.get("over_rejection_detected") is False
    )
    return {
        "full_state_consistency_passed": passed,
        "persisted_state_support_level": support_level,
        "max_abs_metric_delta": round(max_abs, 6),
        "allowed_delta": allowed_delta,
        "metric_delta_summary": deltas,
        "degraded_metrics": degraded,
        "improved_metrics": improved,
        "consistency_failure_reason": _reason(passed, support_level, same_process, cross_process, external_ood, multiseed, forbidden_scan, degraded),
    }


def _reason(passed, support_level, same_process, cross_process, external_ood, multiseed, forbidden_scan, degraded):
    if passed:
        return None
    if support_level != "full_router_root":
        return "persisted_state_support_level_not_full_router_root"
    if forbidden_scan.get("forbidden_field_in_state_count", 1):
        return "forbidden_fields_in_state"
    if cross_process.get("cross_process_reload_passed") is not True:
        return "cross_process_reload_failed"
    if external_ood.get("overall_ood_false_accept_rate", 1.0) > 0.10:
        return "external_ood_failed"
    if multiseed.get("stable_across_seeds") is not True:
        return "multiseed_unstable"
    if same_process.get("over_rejection_detected"):
        return "over_rejection_detected"
    if degraded:
        return "metric_degraded"
    return "unknown"
