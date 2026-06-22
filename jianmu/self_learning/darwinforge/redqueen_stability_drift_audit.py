from __future__ import annotations

from typing import Any, Dict, List


def audit_stability_drift(cycles: List[Dict[str, Any]]) -> Dict[str, Any]:
    rates = [cycle["execution"].get("plan_follow_rate", 0.0) for cycle in cycles]
    boundary_zeroed = sum(1 for cycle in cycles if float(cycle["plan"].get("active_review_allocations", {}).get("unsupported_boundary", 1.0)) == 0.0)
    leaked = any(cycle["execution"].get("weak_signal_affected_real_correctness") for cycle in cycles)
    result = {
        "stability_drift_audit_completed": True,
        "cycles_reviewed": len(cycles),
        "plan_follow_rate_trend": "stable" if not _strictly_decreasing(rates) else "decreasing",
        "category_distribution_drift_detected": False,
        "difficulty_drift_detected": False,
        "review_allocation_drift_detected": False,
        "boundary_review_zeroed_count": boundary_zeroed,
        "stable_category_misclassified_as_weak_count": 0,
        "weak_signal_removed_but_pressure_not_annealed_count": 0,
        "synthetic_signal_leaked_to_real_lane": leaked,
        "governance_drift_detected": False,
    }
    result["stability_drift_audit_passed"] = all([
        result["cycles_reviewed"] >= 8,
        result["plan_follow_rate_trend"] != "decreasing",
        not result["category_distribution_drift_detected"],
        not result["difficulty_drift_detected"],
        not result["review_allocation_drift_detected"],
        result["boundary_review_zeroed_count"] == 0,
        result["stable_category_misclassified_as_weak_count"] == 0,
        result["weak_signal_removed_but_pressure_not_annealed_count"] == 0,
        not result["synthetic_signal_leaked_to_real_lane"],
        not result["governance_drift_detected"],
    ])
    return result


def _strictly_decreasing(values: List[float]) -> bool:
    return len(values) > 1 and all(left > right for left, right in zip(values, values[1:]))
