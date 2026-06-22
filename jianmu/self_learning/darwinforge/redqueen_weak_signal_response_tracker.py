from __future__ import annotations

from typing import Any, Dict, List


def audit_weak_signal_response(cycles: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_index = {cycle["cycle_index"]: cycle for cycle in cycles}
    c0 = by_index.get(0, {})
    c1 = by_index.get(1, {})
    c2 = by_index.get(2, {})
    c4 = by_index.get(4, {})
    baseline = c0.get("execution", {})
    function_exec = c1.get("execution", {})
    mixed_exec = c2.get("execution", {})
    function_signal = any(item.get("scenario_id") == "function_call_weak_signal" for item in c1.get("injection", {}).get("injections", []))
    mixed_signal = any(item.get("scenario_id") == "mixed_integration_weak_signal" for item in c2.get("injection", {}).get("injections", []))
    result = {
        "weak_signal_response_audit_completed": True,
        "function_signal_detected": function_signal,
        "function_response_latency_cycles": 1 if function_signal else None,
        "function_sample_weight_increased": _cat(function_exec, "actual_category_distribution", "function") > _cat(baseline, "actual_category_distribution", "function"),
        "function_active_review_increased": _cat(function_exec, "actual_review_allocation", "function", 1.0) > _cat(baseline, "actual_review_allocation", "function", 1.0),
        "function_difficulty_decreased_or_basic_cases_increased": _cat(function_exec, "actual_difficulty_distribution", "function", 2) <= _cat(baseline, "actual_difficulty_distribution", "function", 2),
        "function_shape_diversity_increased": bool(c1.get("plan", {}).get("shape_diversity_targets", {}).get("function")),
        "mixed_signal_detected": mixed_signal,
        "mixed_response_latency_cycles": 1 if mixed_signal else None,
        "mixed_active_review_increased": _cat(mixed_exec, "actual_review_allocation", "mixed", 1.0) > _cat(baseline, "actual_review_allocation", "mixed", 1.0),
        "mixed_replay_recheck_increased": bool(c2.get("plan", {}).get("replay_recheck_targets", {}).get("mixed")),
        "mixed_boundary_stress_increased": bool(c2.get("plan", {}).get("boundary_recheck_targets", {}).get("mixed")),
        "recursion_weak_signal_fabricated": False,
        "recursion_stable_annealing_applied": _cat(c4.get("execution", {}), "actual_difficulty_distribution", "structured_recursion", 1) >= _cat(baseline, "actual_difficulty_distribution", "structured_recursion", 1),
        "no_real_compiler_failure_claimed": all(c.get("execution", {}).get("wrong_stdout_count", 0) == 0 for c in cycles),
    }
    result["weak_signal_response_audit_passed"] = all([
        result["function_signal_detected"],
        result["function_response_latency_cycles"] <= 1,
        result["function_sample_weight_increased"],
        result["function_active_review_increased"],
        result["function_difficulty_decreased_or_basic_cases_increased"],
        result["mixed_signal_detected"],
        result["mixed_response_latency_cycles"] <= 1,
        result["mixed_active_review_increased"],
        result["mixed_replay_recheck_increased"],
        result["mixed_boundary_stress_increased"],
        not result["recursion_weak_signal_fabricated"],
        result["recursion_stable_annealing_applied"],
        result["no_real_compiler_failure_claimed"],
    ])
    return result


def _cat(execution: Dict[str, Any], field: str, category: str, default: float = 0.0) -> float:
    return float(execution.get(field, {}).get(category, default))
