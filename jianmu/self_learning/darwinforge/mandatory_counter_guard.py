from __future__ import annotations

from typing import Any, Dict, List


def assess_mandatory_counters(counters: Dict[str, Any], wall_clock_runtime_seconds: float, mode_status: str = "completed", minimum_plausible_runtime_seconds: float = 0.001) -> Dict[str, Any]:
    """Validate whether a real mode can honestly be marked completed."""
    blocking: List[str] = []
    partial_reason = counters.get("partial_count_reason")
    partial = mode_status == "partial" or bool(partial_reason)
    for reported_key, actual_key, label in [
        ("reported_train_count", "actual_train_iterated_count", "train"),
        ("reported_eval_count", "actual_eval_iterated_count", "eval"),
        ("reported_external_ood_count", "actual_external_ood_iterated_count", "external_ood"),
    ]:
        reported = int(counters.get(reported_key, 0) or 0)
        actual = int(counters.get(actual_key, 0) or 0)
        if reported > 0 and actual == 0:
            blocking.append(f"{label} reported {reported} but actual iteration count is zero")
        if not partial and actual < reported:
            blocking.append(f"{label} actual count {actual} is below reported count {reported}")
    for key in [
        "freebeam_eval_call_count",
        "canonicalizer_call_count",
        "branchchain_route_call_count",
        "runtime_capture_event_count",
        "cross_process_child_eval_count",
    ]:
        if int(counters.get(key, 0) or 0) <= 0:
            blocking.append(f"{key} must be > 0")
    if counters.get("synthetic_summary_detected"):
        blocking.append("synthetic summary path detected")
    if counters.get("fixed_metric_detected"):
        blocking.append("fixed metric path detected")
    suspicious_runtime = wall_clock_runtime_seconds < minimum_plausible_runtime_seconds
    if suspicious_runtime:
        blocking.append("wall clock runtime is below minimum plausible runtime")
    passed = not blocking
    return {
        "mandatory_counter_guard_passed": passed,
        "mode_status": "completed" if passed and not partial else ("partial" if partial and not any("zero" in issue for issue in blocking) else "invalid"),
        "blocking_issues": blocking,
        "suspicious_runtime": suspicious_runtime,
        "partial_count_reason": partial_reason,
    }
