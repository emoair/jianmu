from __future__ import annotations

from typing import Any, Dict, List


def assess_larger_readiness(metrics: Dict[str, Any], progress_summary: Dict[str, Any]) -> Dict[str, Any]:
    blocking: List[str] = []
    if not metrics.get("larger_rerun_completed") and not metrics.get("larger_rerun_partial"):
        blocking.append("larger_rerun_not_completed")
    if not progress_summary.get("metrics_affected_by_progress") is False:
        blocking.append("progress_metrics_not_safe")
    if metrics.get("forbidden_field_access_count", 0) != 0:
        blocking.append("forbidden_field_access")
    if metrics.get("expected_output_access_before_candidate_generation"):
        blocking.append("expected_output_access_before_candidate_generation")
    if metrics.get("target_ir_access_before_candidate_generation"):
        blocking.append("target_ir_access_before_candidate_generation")
    if metrics.get("supported_candidate_hit_after", 0.0) <= metrics.get("supported_candidate_hit_before", 0.0):
        blocking.append("candidate_hit_not_improved")
    if metrics.get("top1_supported_correct_after", 0.0) <= metrics.get("top1_supported_correct_before", 0.0):
        blocking.append("top1_not_improved")
    if metrics.get("heldout_supported_success_rate", 0.0) < 0.3815:
        blocking.append("heldout_below_v0_9_7")
    if not metrics.get("compiler_validation_completed"):
        blocking.append("compiler_validation_not_completed")
    if metrics.get("backend_type") != "real_c_compiler" or metrics.get("compiler_name") != "cl":
        blocking.append("compiler_not_real_cl")
    if metrics.get("compile_worker_count") != 16:
        blocking.append("compile_worker_count_not_16")
    if metrics.get("compiler_verified_correct_rate", 0.0) < 0.98:
        blocking.append("compiler_verified_rate_low")
    for key in ["permission_error_count", "cleanup_failure_count", "boundary_compiler_misroute_count"]:
        if metrics.get(key, 0) != 0:
            blocking.append(key)
    if not metrics.get("cross_process_reload_passed"):
        blocking.append("cross_process_reload_failed")
    if metrics.get("synthetic_summary_detected") or metrics.get("fixed_metric_detected") or metrics.get("periodic_rule_detected"):
        blocking.append("metric_provenance_failed")
    if blocking:
        if "compiler_verified_rate_low" in blocking or "permission_error_count" in blocking:
            claim = "needs_failure_taxonomy"
        elif "candidate_hit_not_improved" in blocking or "top1_not_improved" in blocking:
            claim = "boundary_safe_but_no_larger_gain"
        else:
            claim = "bounded_substrate_larger_mixed_signal"
    else:
        claim = "bounded_substrate_larger_positive_signal"
    return {
        "larger_rerun_attempted": True,
        "larger_rerun_completed": metrics.get("larger_rerun_completed", False),
        "larger_rerun_partial": metrics.get("larger_rerun_partial", False),
        "partial_reason": metrics.get("partial_reason", ""),
        "dataset_scales_used": metrics.get("dataset_scales_used", []),
        "seeds_completed": metrics.get("seeds_completed", []),
        "progress_enabled": progress_summary.get("progress_enabled", False),
        "progress_metrics_safe": progress_summary.get("metrics_affected_by_progress") is False,
        "persisted_state_support_level": metrics.get("persisted_state_support_level"),
        "cross_process_reload_passed": metrics.get("cross_process_reload_passed", False),
        "compiler_validation_completed": metrics.get("compiler_validation_completed", False),
        "backend_type": metrics.get("backend_type"),
        "compiler_name": metrics.get("compiler_name"),
        "compile_worker_count": metrics.get("compile_worker_count"),
        "real_compiler_invocation_count": metrics.get("real_compiler_invocation_count", 0),
        "compiler_verified_correct_rate": metrics.get("compiler_verified_correct_rate", 0.0),
        "permission_error_count": metrics.get("permission_error_count", 0),
        "cleanup_failure_count": metrics.get("cleanup_failure_count", 0),
        "boundary_compiler_misroute_count": metrics.get("boundary_compiler_misroute_count", 0),
        "forbidden_field_access_count": metrics.get("forbidden_field_access_count", 0),
        "supported_candidate_hit_before": metrics.get("supported_candidate_hit_before", 0.0),
        "supported_candidate_hit_after": metrics.get("supported_candidate_hit_after", 0.0),
        "top1_before": metrics.get("top1_supported_correct_before", 0.0),
        "top1_after": metrics.get("top1_supported_correct_after", 0.0),
        "heldout_supported_success_rate": metrics.get("heldout_supported_success_rate", 0.0),
        "baseline_gap_verified": metrics.get("baseline_gap_verified", False),
        "synthetic_summary_detected": metrics.get("synthetic_summary_detected", False),
        "fixed_metric_detected": metrics.get("fixed_metric_detected", False),
        "periodic_rule_detected": metrics.get("periodic_rule_detected", False),
        "recommended_claim_level": claim,
        "blocking_issues": blocking,
        "required_next_run": "larger independent rerun on another machine or longer bounded substrate probe; still no Turing-completeness claim",
    }

