from __future__ import annotations

from typing import Any, Dict


def audit_overreaction(pre_metrics: Dict[str, Any], post_metrics: Dict[str, Any], execution: Dict[str, Any]) -> Dict[str, Any]:
    pre = {item["category"]: item for item in pre_metrics.get("categories", [])}
    actual_review = execution.get("actual_review_allocation", {})
    actual_diff = execution.get("actual_difficulty_distribution", {})
    stable_zeroed = 0
    difficulty_jump = 0
    boundary_zeroed = 0
    weight_jump = 0
    for category, item in pre.items():
        pre_weight = float(item.get("review_weight", 1.0))
        post_weight = float(actual_review.get(category, pre_weight))
        if pre_weight and post_weight / pre_weight > 3 and item.get("success_rate", 1.0) >= 0.995:
            weight_jump += 1
        if item.get("success_rate", 1.0) >= 0.995 and post_weight == 0:
            stable_zeroed += 1
        if abs(int(actual_diff.get(category, item.get("difficulty_level", 1))) - int(item.get("difficulty_level", 1))) > 2:
            difficulty_jump += 1
        if category in {"default_blocking", "unsupported_boundary"} and execution.get("actual_category_distribution", {}).get(category, 0) == 0:
            boundary_zeroed += 1
    return {
        "overreaction_audit_completed": True,
        "overreaction_detected": any([stable_zeroed, difficulty_jump, boundary_zeroed, weight_jump]),
        "stable_category_zeroed_count": stable_zeroed,
        "difficulty_jump_too_large_count": difficulty_jump,
        "boundary_review_zeroed_count": boundary_zeroed,
        "weight_jump_without_risk_count": weight_jump,
    }
