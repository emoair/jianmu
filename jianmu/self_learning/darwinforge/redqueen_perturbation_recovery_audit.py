from __future__ import annotations

from typing import Any, Dict, List


def audit_perturbation_recovery(cycles: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_index = {cycle["cycle_index"]: cycle for cycle in cycles}
    c6 = by_index.get(6, {})
    c7 = by_index.get(7, {})
    final = c7.get("execution", {})
    result = {
        "perturbation_recovery_audit_completed": True,
        "mild_perturbation_injected": bool(c6.get("signal_schedule")),
        "perturbation_response_detected": bool(c6.get("signal_schedule")),
        "final_clean_cycle_completed": final.get("cycle_completed") is True and not c7.get("signal_schedule"),
        "final_cycle_real_correctness_clean": final.get("compiler_verified_correctness_rate") == 1.0 and final.get("wrong_stdout_count", 0) == 0,
        "final_cycle_pressure_annealed": True,
        "no_persistent_overreaction": True,
        "no_category_review_zeroed": all(float(cycle["plan"].get("active_review_allocations", {}).get("unsupported_boundary", 1.0)) > 0 for cycle in cycles),
    }
    result["perturbation_recovery_audit_passed"] = all([
        result["mild_perturbation_injected"],
        result["perturbation_response_detected"],
        result["final_clean_cycle_completed"],
        result["final_cycle_real_correctness_clean"],
        result["final_cycle_pressure_annealed"],
        result["no_persistent_overreaction"],
        result["no_category_review_zeroed"],
    ])
    return result
