from __future__ import annotations

from typing import Any, Dict, List


def assess_real_longrun_readiness(summary: Dict[str, Any]) -> Dict[str, Any]:
    blocking: List[str] = []
    large_completed = summary.get("real_large_completed", False)
    xlarge_completed = summary.get("real_xlarge_completed", False)
    if not large_completed:
        blocking.append("large-real did not complete")
    for key in [
        "mandatory_counter_guard_passed",
        "cross_process_real_execution_verified",
        "runtime_plausibility_passed",
    ]:
        if not summary.get(key):
            blocking.append(f"{key} is false")
    if summary.get("supported_retention_rate", 0.0) < 0.98:
        blocking.append("supported retention below 0.98")
    if summary.get("external_ood_false_accept_rate", 1.0) > 0.10:
        blocking.append("external OOD false accept above 0.10")
    if summary.get("forbidden_field_in_state_count", 1) != 0:
        blocking.append("forbidden fields detected")
    if summary.get("synthetic_summary_detected"):
        blocking.append("synthetic summary detected")
    if summary.get("fixed_metric_detected"):
        blocking.append("fixed metric detected")
    if xlarge_completed and not blocking:
        level = "real_xlarge_verified"
    elif large_completed and not blocking:
        level = "real_large_verified"
    elif summary.get("largest_partial_real_mode"):
        level = "partial_real_longrun"
    elif summary.get("largest_completed_real_mode") == "real-mini":
        level = "needs_more_runtime"
    else:
        level = "failed"
    return {
        "real_longrun_completed": large_completed or xlarge_completed,
        "real_large_completed": large_completed,
        "real_xlarge_completed": xlarge_completed,
        "ready_for_real_longrun_claim": not blocking and large_completed,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "" if not blocking else "rerun large-real with mandatory counters until all guards pass",
    }
