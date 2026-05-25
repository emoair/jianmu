from __future__ import annotations

from typing import Any, Dict, List


def assess_nonperiodic_readiness(metrics: Dict[str, Any]) -> Dict[str, Any]:
    blocking: List[str] = []
    if not metrics.get("nonperiodic_rerun_completed"):
        blocking.append("nonperiodic rerun did not complete")
    if not metrics.get("per_sample_trace_completed"):
        blocking.append("per-sample candidate trace missing")
    if not metrics.get("metric_provenance_passed"):
        blocking.append("metric provenance failed")
    if not metrics.get("leakage_guard_passed"):
        blocking.append("leakage guard failed")
    if metrics.get("periodic_rule_detected"):
        blocking.append("periodic rule detected")
    if metrics.get("fixed_value_detected"):
        blocking.append("fixed value detected")
    if metrics.get("summary_only_detected"):
        blocking.append("summary-only metric detected")
    if not metrics.get("boundary_safety_preserved"):
        blocking.append("boundary safety not preserved")
    gain = metrics.get("top1_after", 0.0) - metrics.get("top1_before", 0.0)
    if gain <= 0.02:
        blocking.append("top1 gain below meaningful margin")
    if not metrics.get("baseline_gap_verified"):
        level = "nonperiodic_arithmetic_mixed_signal" if gain > 0.02 and not metrics.get("periodic_rule_detected") else "signal_not_verified"
    elif blocking:
        level = "signal_not_verified" if any("periodic" in issue or "fixed" in issue or "summary" in issue for issue in blocking) else "nonperiodic_arithmetic_mixed_signal"
    else:
        level = "nonperiodic_arithmetic_positive_signal"
    if metrics.get("boundary_safety_preserved") and gain <= 0.02:
        level = "boundary_safe_but_no_arithmetic_gain"
    return {
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": _required_next_run(metrics, blocking),
        "ready_for_nonperiodic_claim": level == "nonperiodic_arithmetic_positive_signal",
    }


def _required_next_run(metrics: Dict[str, Any], blocking: List[str]) -> str:
    required = []
    if metrics.get("internal_evaluator_only"):
        required.append("real compiler-backed arithmetic spot audit")
    if not metrics.get("baseline_gap_verified"):
        required.append("stronger baseline/ablation rerun with per-sample traces")
    if blocking:
        required.append("repeat nonperiodic rerun after resolving blockers")
    return "; ".join(required)
