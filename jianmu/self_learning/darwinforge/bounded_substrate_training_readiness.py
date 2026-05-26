from __future__ import annotations

from typing import Any, Dict, List


def assess_bounded_substrate_readiness(metrics: Dict[str, Any]) -> Dict[str, Any]:
    blocking: List[str] = []
    if metrics.get("forbidden_field_access_count", 0) != 0:
        blocking.append("forbidden_field_access")
    if not metrics.get("mandatory_counter_guard_passed"):
        blocking.append("mandatory_counter_guard_failed")
    if metrics.get("persisted_state_support_level") != "full_router_root":
        blocking.append("state_not_full_router_root")
    if not metrics.get("cross_process_reload_passed"):
        blocking.append("cross_process_reload_failed")
    if metrics.get("supported_candidate_hit_after", 0) <= metrics.get("supported_candidate_hit_before", 0):
        blocking.append("candidate_hit_not_improved")
    if metrics.get("top1_supported_correct_after", 0) <= metrics.get("top1_supported_correct_before", 0):
        blocking.append("top1_not_improved")
    if metrics.get("backend_type") != "real_c_compiler" or metrics.get("compile_worker_count") != 16:
        blocking.append("compiler_validation_not_real_16_worker")
    for key in [
        "boundary_compiler_misroute_count",
        "unbounded_loop_false_accept_rate",
        "recursion_false_accept_rate",
        "pointer_false_accept_rate",
        "array_false_accept_rate",
        "function_false_accept_rate",
    ]:
        if metrics.get(key, 0) != 0:
            blocking.append(key)
    if metrics.get("synthetic_summary_detected") or metrics.get("fixed_metric_detected") or metrics.get("periodic_rule_detected"):
        blocking.append("metric_provenance_failed")
    if blocking:
        claim = "signal_not_verified" if "metric_provenance_failed" in blocking else "bounded_substrate_probe_mixed_signal"
    else:
        claim = "bounded_substrate_probe_positive_signal"
    return {
        "ready_for_bounded_substrate_probe_claim": not blocking,
        "recommended_claim_level": claim,
        "blocking_issues": blocking,
        "required_next_run": "larger bounded substrate rerun with compiler validation; still no Turing-completeness claim",
    }
