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


def check_runtime_state_consistency(
    v087_metrics: Dict,
    v088_metrics: Dict,
    v089_metrics: Dict,
    same_process: Dict,
    cross_process: Dict,
    external_ood: Dict,
    multiseed: Dict,
    forbidden_scan: Dict,
    support_level: str,
    figure_data_pack_generated: bool = False,
    allowed_delta: float = 0.02,
) -> Dict:
    base = v087_metrics or v088_metrics or v089_metrics or {}
    same_metrics = same_process.get("metrics", same_process)
    deltas = {}
    degraded: List[str] = []
    for name in TRACKED:
        old = float(base.get(name, same_metrics.get(name, 0.0)) or 0.0)
        new = float(same_metrics.get(name, 0.0) or 0.0)
        delta = round(new - old, 6)
        deltas[name] = delta
        if delta < -allowed_delta:
            degraded.append(name)
    max_abs = max((abs(value) for value in deltas.values()), default=0.0)
    blockers = []
    if support_level != "full_router_root":
        blockers.append("persisted_state_support_level_not_full_router_root")
    if not same_process.get("same_process_reload_passed", same_process.get("no_label_inference_passed", False)):
        blockers.append("same_process_reload_failed")
    if not cross_process.get("cross_process_reload_passed"):
        blockers.append("cross_process_reload_failed")
    if forbidden_scan.get("forbidden_field_in_state_count", 1) != 0:
        blockers.append("forbidden_fields_in_state")
    if external_ood.get("overall_ood_false_accept_rate", 1.0) > 0.10:
        blockers.append("external_ood_failed")
    if not multiseed.get("stable_across_seeds", False):
        blockers.append("multiseed_unstable")
    if same_process.get("current_supported_retention_rate", 0.0) < 0.98:
        blockers.append("supported_retention_not_preserved")
    if same_process.get("over_rejection_detected", False):
        blockers.append("over_rejection_detected")
    if not figure_data_pack_generated:
        blockers.append("paper_figure_data_pack_missing")
    if degraded:
        blockers.append("metric_degraded")
    return {
        "runtime_full_state_consistency_passed": not blockers,
        "persisted_state_support_level": support_level,
        "max_abs_metric_delta": round(max_abs, 6),
        "allowed_delta": allowed_delta,
        "metric_delta_summary": deltas,
        "degraded_metrics": degraded,
        "consistency_failure_reason": blockers[0] if blockers else None,
        "readiness_blockers": blockers,
    }
