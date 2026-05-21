from __future__ import annotations

from typing import Dict, List

from jianmu.self_learning.darwinforge.boundary_metrics import compute_boundary_metrics


def compute_boundary_generalization_metrics(samples: List[Dict], decisions: List[Dict], probe_metrics: Dict | None = None) -> Dict:
    metrics = compute_boundary_metrics(samples, decisions, [])
    supported_count = sum(1 for row in samples if row.get("boundary_label") == "current_supported")
    false_reject_supported = sum(
        1 for sample, decision in zip(samples, decisions) if sample.get("boundary_label") == "current_supported" and decision.get("rejected")
    )
    metrics["over_rejection_rate"] = round(false_reject_supported / supported_count, 6) if supported_count else 0.0
    if probe_metrics:
        after = probe_metrics.get("after_metrics", probe_metrics)
        metrics.update(
            {
                "delta_current_supported_retention": round(metrics["current_supported_retention_rate"] - after.get("current_supported_retention_rate", 0), 6),
                "delta_ood_false_accept": round(metrics["overall_ood_false_accept_rate"] - after.get("overall_ood_false_accept_rate", 0), 6),
                "delta_hard_ood_rejection": round(metrics["hard_ood_rejection_rate"] - after.get("hard_ood_rejection_rate", 0), 6),
                "delta_trap_rejection": round(metrics["true_false_accept_trap_rejection_rate"] - after.get("true_false_accept_trap_rejection_rate", 0), 6),
                "delta_future_domain_isolation": round(metrics["future_domain_isolation_rate"] - after.get("future_domain_isolation_rate", 0), 6),
                "delta_near_ood_quarantine": round(metrics["near_ood_quarantine_rate"] - after.get("near_ood_quarantine_rate", 0), 6),
            }
        )
    return metrics
