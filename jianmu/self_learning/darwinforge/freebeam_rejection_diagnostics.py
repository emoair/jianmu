from __future__ import annotations

from collections import Counter
from typing import Dict, List


def diagnose_freebeam_rejection(metrics: Dict, decisions: List[Dict], no_label_guard: Dict, metadata: Dict | None = None) -> Dict:
    metadata = metadata or {}
    over_rejection = metrics.get("current_supported_retention_rate", 0.0) < 0.98
    confirmed = (
        no_label_guard.get("no_label_inference_passed") is True
        and metrics.get("hard_ood_rejection_rate", 0.0) >= 0.80
        and metrics.get("true_false_accept_trap_rejection_rate", 0.0) >= 0.80
        and metrics.get("overall_ood_false_accept_rate", 1.0) <= 0.25
        and metrics.get("current_supported_retention_rate", 0.0) >= 0.98
        and not over_rejection
        and metadata.get("hardcoded_rejection_gate_added") is not True
        and metadata.get("real_promotion_enabled") is not True
    )
    partial = (
        not confirmed
        and metrics.get("current_supported_retention_rate", 0.0) >= 0.98
        and (
            metrics.get("hard_ood_rejection_rate", 0.0) >= 0.5
            or metrics.get("true_false_accept_trap_rejection_rate", 0.0) >= 0.5
        )
    )
    failed = not confirmed and metrics.get("overall_ood_false_accept_rate", 1.0) > 0.25
    return {
        "freebeam_emergent_rejection_signal_confirmed": confirmed,
        "partial_boundary_generalization": partial,
        "boundary_probe_did_not_generalize": failed,
        "over_rejection_detected": over_rejection,
        "rejection_layer_distribution": dict(Counter(row.get("rejection_layer", "unknown") for row in decisions)),
        "false_accept_examples": [row for row in decisions if row.get("error_type") == "false_accept_boundary"][:20],
        "false_reject_supported_examples": [row for row in decisions if row.get("error_type") == "false_reject_supported"][:20],
        "future_domain_misclassified_examples": [
            row for row in decisions if row.get("evaluation", {}).get("boundary_label") == "future_domain_candidate" and row.get("error_type") != "none"
        ][:20],
        "near_ood_misclassified_examples": [
            row for row in decisions if row.get("evaluation", {}).get("boundary_label") == "near_ood_generalization_candidate" and row.get("error_type") != "none"
        ][:20],
    }
