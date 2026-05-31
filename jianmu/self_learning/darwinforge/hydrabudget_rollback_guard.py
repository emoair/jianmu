from __future__ import annotations

from typing import Any, Dict


def evaluate_rollback(baseline_top1: float, new_top1: float, baseline_miss: float, new_miss: float, boundary_false_accept: float = 0.0, bad_route_amplification: bool = False) -> Dict[str, Any]:
    rollback = new_top1 < baseline_top1 - 0.005 or new_miss > baseline_miss or boundary_false_accept > 0 or bad_route_amplification
    reasons = []
    if new_top1 < baseline_top1 - 0.005:
        reasons.append("top1_regression")
    if new_miss > baseline_miss:
        reasons.append("candidate_miss_regression")
    if boundary_false_accept > 0:
        reasons.append("boundary_regression")
    if bad_route_amplification:
        reasons.append("bad_route_amplification")
    return {"rollback_required": rollback, "rollback_reasons": reasons}

