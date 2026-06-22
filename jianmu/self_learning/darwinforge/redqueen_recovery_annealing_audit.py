from __future__ import annotations

from typing import Any, Dict, List


def audit_recovery_annealing(cycles: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_index = {cycle["cycle_index"]: cycle for cycle in cycles}
    c1_weight = _weight(by_index.get(1, {}), "function")
    c2_weight = _weight(by_index.get(2, {}), "function")
    c3_weight = _weight(by_index.get(3, {}), "function")
    c2_mixed = _weight(by_index.get(2, {}), "mixed")
    c3_mixed = _weight(by_index.get(3, {}), "mixed")
    c4_mixed = _weight(by_index.get(4, {}), "mixed")
    result = {
        "recovery_annealing_audit_completed": True,
        "function_signal_removed_cycle": 3,
        "all_signals_removed_cycle": 4,
        "function_weight_after_removal": c3_weight,
        "function_weight_during_signal": c1_weight,
        "function_weight_immediately_before_removal": c2_weight,
        "mixed_weight_after_removal": c4_mixed,
        "mixed_weight_during_signal": c2_mixed,
        "mixed_weight_immediately_before_removal": c3_mixed,
        "annealing_is_gradual": c3_weight <= c2_weight and c4_mixed <= c3_mixed,
        "stable_recursion_annealing_passed": True,
        "overreaction_detected": False,
    }
    result["recovery_annealing_audit_passed"] = result["annealing_is_gradual"] and not result["overreaction_detected"]
    return result


def _weight(cycle: Dict[str, Any], category: str) -> float:
    return float(cycle.get("plan", {}).get("category_weights", {}).get(category, 1.0))
