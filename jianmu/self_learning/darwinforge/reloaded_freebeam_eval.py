from __future__ import annotations

from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.boundary_generalization_metrics import compute_boundary_generalization_metrics
from jianmu.self_learning.darwinforge.freebeam_boundary_eval import FreeBeamConfig, run_freebeam_boundary_eval
from jianmu.self_learning.darwinforge.freebeam_rejection_diagnostics import diagnose_freebeam_rejection
from jianmu.self_learning.darwinforge.no_label_inference_guard import assert_no_label_fields_used


RELOADED_MODE_CONFIGS = {
    "quick": {"eval_limit": 1000, "worker_count": 4, "beam_size": 64, "top_k": 5},
    "medium": {"eval_limit": 3000, "worker_count": 4, "beam_size": 96, "top_k": 8},
    "large": {"eval_limit": 8000, "worker_count": 4, "beam_size": 128, "top_k": 10},
}


def run_reloaded_freebeam_eval(samples: List[Dict[str, Any]], persisted_state: Dict[str, Any], mode: str = "quick", worker_count: int = 4) -> Dict[str, Any]:
    cfg = FreeBeamConfig.for_mode(mode, worker_count=worker_count)
    training_summary = _training_summary_from_state(persisted_state)
    eval_result = run_freebeam_boundary_eval(samples, training_summary, cfg)
    guard = assert_no_label_fields_used(eval_result["feature_access"])
    metrics = compute_boundary_generalization_metrics(samples[: cfg.eval_limit], eval_result["decisions"], training_summary)
    diagnostics = diagnose_freebeam_rejection(
        metrics,
        eval_result["decisions"],
        guard,
        {"real_promotion_enabled": False, "hardcoded_rejection_gate_added": False},
    )
    if not any(row.get("boundary_label") == "current_supported" for row in samples[: cfg.eval_limit]):
        diagnostics["over_rejection_detected"] = False
    return {
        "mode": mode,
        "reloaded_eval_completed": True,
        "persisted_state_support_level": persisted_state.get("persisted_state_support_level", "unavailable"),
        "no_label_inference_passed": guard["no_label_inference_passed"],
        "forbidden_field_access_count": guard["forbidden_field_access_count"],
        "guard": guard,
        "metrics": metrics,
        "diagnostics": diagnostics,
        "decisions": eval_result["decisions"],
        "current_supported_retention_rate": metrics["current_supported_retention_rate"],
        "hard_ood_rejection_rate": metrics["hard_ood_rejection_rate"],
        "true_false_accept_trap_rejection_rate": metrics["true_false_accept_trap_rejection_rate"],
        "future_domain_isolation_rate": metrics["future_domain_isolation_rate"],
        "near_ood_quarantine_rate": metrics["near_ood_quarantine_rate"],
        "overall_ood_false_accept_rate": metrics["overall_ood_false_accept_rate"],
        "false_accept_examples_count": len(diagnostics["false_accept_examples"]),
        "false_reject_supported_examples_count": len(diagnostics["false_reject_supported_examples"]),
        "over_rejection_detected": diagnostics["over_rejection_detected"],
        "real_promotion_enabled": False,
        "hardcoded_rejection_gate_added": False,
    }


def _training_summary_from_state(persisted_state: Dict[str, Any]) -> Dict[str, Any]:
    files = persisted_state.get("state_files", {})
    summary = files.get("training_summary.json", {}).get("summary", {})
    summary["available"] = summary.get("available", True)
    summary["reloaded_from_persisted_state"] = True
    return summary
