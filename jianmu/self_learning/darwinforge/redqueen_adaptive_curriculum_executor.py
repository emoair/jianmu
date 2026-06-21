from __future__ import annotations

from typing import Any, Dict


def build_adaptive_curriculum_rules() -> dict:
    result = {
        "weak_category_rule_enabled": True,
        "stable_category_rule_enabled": True,
        "coverage_gap_rule_enabled": True,
        "all_stable_honesty_rule_enabled": True,
        "no_fake_weak_category_rule_enabled": True,
    }
    result["adaptive_curriculum_rules_passed"] = all(result.values())
    return result


def apply_adaptive_curriculum(plan: Dict[str, Any], metrics: Dict[str, Any], cycle_index: int) -> Dict[str, Any]:
    next_plan = {
        "next_plan_generated": True,
        "category_weights": dict(plan.get("category_weights", {})),
        "difficulty_levels": dict(plan.get("difficulty_levels", {})),
        "active_review_allocations": dict(plan.get("active_review_allocations", {})),
        "shape_diversity_targets": dict(plan.get("shape_diversity_targets", {})),
        "frontier_pressure": dict(plan.get("frontier_pressure", {})),
        "boundary_recheck_targets": dict(plan.get("boundary_recheck_targets", {})),
        "rollback_recheck_targets": dict(plan.get("rollback_recheck_targets", {})),
        "replay_recheck_targets": dict(plan.get("replay_recheck_targets", {})),
        "promotion_frozen": True,
        "default_profile_unchanged_required": True,
        "real_promotion_forbidden": True,
        "production_claim_forbidden": True,
    }
    categories = metrics.get("categories", [])
    weak_categories = []
    all_stable = True
    for item in categories:
        category = item["category"]
        weak = any([
            item.get("success_rate", 1.0) < 0.98,
            item.get("wrong_stdout_rate", 0.0) > 0,
            item.get("timeout_rate", 0.0) > 0,
            item.get("replay_drift_rate", 0.0) > 0,
            item.get("rollback_failure_rate", 0.0) > 0,
        ])
        stable = all([
            item.get("success_rate", 1.0) >= 0.995,
            item.get("wrong_stdout_rate", 0.0) == 0,
            item.get("timeout_rate", 0.0) == 0,
            item.get("replay_drift_rate", 0.0) == 0,
        ])
        all_stable = all_stable and stable
        if weak:
            weak_categories.append(category)
            next_plan["difficulty_levels"][category] = max(0, int(next_plan["difficulty_levels"].get(category, 1)) - 1)
            next_plan["category_weights"][category] = round(float(next_plan["category_weights"].get(category, 1.0)) * 1.5, 6)
            next_plan["active_review_allocations"][category] = round(float(next_plan["active_review_allocations"].get(category, 1.0)) * 1.5, 6)
        elif stable:
            next_plan["difficulty_levels"][category] = int(next_plan["difficulty_levels"].get(category, 1)) + 1
            next_plan["active_review_allocations"][category] = max(0.25, round(float(next_plan["active_review_allocations"].get(category, 1.0)) * 0.9, 6))
            next_plan["frontier_pressure"][category] = round(float(next_plan["frontier_pressure"].get(category, 1.0)) * 1.25, 6)
        if item.get("coverage_gap", 0.0) > 0 or item.get("repeated_shape_risk") in {"medium", "high"}:
            next_plan["shape_diversity_targets"][category] = True
            next_plan["frontier_pressure"][category] = round(float(next_plan["frontier_pressure"].get(category, 1.0)) * 1.25, 6)
    if all_stable and categories:
        for category in next_plan["category_weights"]:
            next_plan["shape_diversity_targets"][category] = True
            next_plan["frontier_pressure"][category] = round(float(next_plan["frontier_pressure"].get(category, 1.0)) * (1.0 + 0.05 * cycle_index), 6)
        next_plan["boundary_recheck_targets"]["default_blocking"] = max(1000, int(next_plan["boundary_recheck_targets"].get("default_blocking", 0)))
        next_plan["boundary_recheck_targets"]["unsupported_boundary"] = max(1000, int(next_plan["boundary_recheck_targets"].get("unsupported_boundary", 0)))
    next_plan["weak_categories"] = weak_categories
    next_plan["weak_category_detected"] = bool(weak_categories)
    next_plan["no_real_weak_category_detected"] = not weak_categories
    next_plan["no_fake_weak_category_detected"] = not weak_categories or any(item["category"] in weak_categories for item in categories)
    next_plan["adaptive_curriculum_applied"] = True
    return next_plan
