from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List


def active_signal_ids_for_cycle(cycle_index: int, schedule: Dict[str, List[str]]) -> List[str]:
    return list(schedule.get(f"cycle_{cycle_index}", []))


def inject_controlled_weak_signals(plan: Dict[str, Any], scenarios: Iterable[Dict[str, Any]], active_signal_ids: Iterable[str]) -> Dict[str, Any]:
    active = set(active_signal_ids)
    next_plan = deepcopy(plan)
    weights = next_plan.setdefault("category_weights", {})
    difficulty = next_plan.setdefault("difficulty_levels", {})
    review = next_plan.setdefault("active_review_allocations", {})
    diversity = next_plan.setdefault("shape_diversity_targets", {})
    replay = next_plan.setdefault("replay_recheck_targets", {})
    boundary = next_plan.setdefault("boundary_recheck_targets", {})
    injections = []
    for scenario in scenarios:
        if scenario["scenario_id"] not in active:
            continue
        category = scenario["category"]
        injections.append(scenario)
        if category == "function":
            weights[category] = round(float(weights.get(category, 1.0)) * 1.12, 4)
            review[category] = round(float(review.get(category, 1.0)) * 1.2, 4)
            difficulty[category] = max(1, int(difficulty.get(category, 2)) - 1)
            diversity[category] = True
        elif category == "mixed":
            weights[category] = round(float(weights.get(category, 1.0)) * 1.1, 4)
            review[category] = round(float(review.get(category, 1.0)) * 1.18, 4)
            replay[category] = True
            boundary[category] = True
        elif category == "structured_recursion":
            difficulty[category] = max(2, int(difficulty.get(category, 2)) + 1)
            review[category] = max(float(review.get(category, 1.0)), 1.0)
    next_plan["controlled_weak_signal_injection_applied"] = bool(injections)
    next_plan["weak_signal_is_synthetic"] = True
    next_plan["weak_signal_affects_real_correctness"] = False
    return {
        "plan": next_plan,
        "injections": injections,
        "weak_signal_injected": bool(injections),
        "weak_signal_is_synthetic": True,
        "weak_signal_affected_real_correctness": False,
    }
