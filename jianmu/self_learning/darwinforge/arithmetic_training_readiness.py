from __future__ import annotations

from typing import Any, Dict, List


def assess_arithmetic_training_readiness(metrics: Dict[str, Any]) -> Dict[str, Any]:
    blocking: List[str] = []
    if "small" not in metrics.get("modes_completed", []):
        blocking.append("small mode did not complete")
    if metrics.get("forbidden_field_access_count", 1) != 0:
        blocking.append("forbidden field access detected")
    if not metrics.get("mandatory_counter_guard_passed"):
        blocking.append("mandatory counter guard failed")
    if metrics.get("persisted_state_support_level") != "full_router_root":
        blocking.append("persisted state is not full_router_root")
    if not metrics.get("cross_process_reload_passed"):
        blocking.append("cross-process reload failed")
    if metrics.get("supported_candidate_hit_after", 0.0) <= metrics.get("supported_candidate_hit_before", 0.0):
        blocking.append("candidate hit did not improve")
    if metrics.get("heldout_supported_success_rate", 0.0) < 0.50:
        blocking.append("heldout supported success below probe threshold")
    if metrics.get("division_by_zero_false_accept_rate", 1.0) != 0:
        blocking.append("division by zero false accept detected")
    if metrics.get("future_domain_supported_accept_rate", 1.0) != 0:
        blocking.append("future domain supported accept detected")
    if metrics.get("synthetic_summary_detected"):
        blocking.append("synthetic summary detected")
    if metrics.get("fixed_metric_detected"):
        blocking.append("fixed metric detected")
    if not blocking:
        level = "arithmetic_probe_positive_signal"
    elif metrics.get("unsupported_false_accept_rate", 1.0) == 0 and metrics.get("supported_candidate_hit_after", 0) <= metrics.get("supported_candidate_hit_before", 0):
        level = "boundary_safe_but_no_arithmetic_gain"
    else:
        level = "needs_more_validation"
    return {
        "ready_for_arithmetic_probe_claim": not blocking,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "" if not blocking else "rerun arithmetic training probe with larger verified counters",
        "no_solved_arithmetic_claim": True,
    }
