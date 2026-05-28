from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def build_billion_state_readiness(
    output_records: str | Path,
    attempted: List[str],
    completed: List[str],
    skipped: Dict[str, str],
    best: Dict[str, Any],
    reference: Dict[str, Any],
    access: Dict[str, Any],
    scaling: Dict[str, Any],
    compiler: Dict[str, Any],
    integrity: Dict[str, Any],
    memory_guard_passed: bool,
    cross_process_reload_passed: bool,
) -> Dict[str, Any]:
    access_rows = {row["profile_name"]: row for row in access.get("profiles", [])}
    state_1b_access = access_rows.get("state_1B", {})
    state_1b_row = best if best.get("profile_name") == "state_1B" else {}
    best_compiler = compiler.get("per_profile", {}).get(best["profile_name"], {})
    blocking = []
    if integrity.get("forbidden_field_access_count", 0):
        blocking.append("forbidden_field_access")
    if best_compiler.get("compiler_verified_correct_rate", 0.0) < 0.98:
        blocking.append("compiler_validation_low")
    if best_compiler.get("boundary_compiler_misroute_count", 0):
        blocking.append("boundary_compiler_misroute")
    one_b_completed = "state_1B" in completed
    one_b_gain = one_b_completed and state_1b_row.get("candidate_miss_rate", 1.0) < reference["candidate_miss_rate"] and state_1b_row.get("top1_correct_rate", 0.0) > reference["top1_correct_rate"]
    low_active = one_b_completed and state_1b_access.get("touch_ratio", 0.0) < 0.03
    if not blocking and one_b_gain and not low_active:
        claim = "billion_state_budget_probe_positive"
    elif not blocking and one_b_completed and low_active:
        claim = "billion_budget_completed_but_low_active_usage"
    elif not blocking and best["profile_name"] != "state_1B" and best["top1_correct_rate"] > reference["top1_correct_rate"]:
        claim = "upper_frontier_positive_below_1B"
    else:
        claim = "upper_frontier_mixed" if not blocking else "failed"
    result = {
        "billion_state_probe_completed": bool(completed),
        "profiles_attempted": attempted,
        "profiles_completed": completed,
        "profiles_skipped": skipped,
        "best_profile_name": best["profile_name"],
        "best_target_state_units": best["target_state_units"],
        "best_actual_state_units_allocated": best["actual_state_units_allocated"],
        "best_materialization_level": best["materialization_level"],
        "state_1B_completed": one_b_completed,
        "state_1B_materialization_level": state_1b_access.get("materialization_level", ""),
        "state_1B_touch_ratio": state_1b_access.get("touch_ratio", 0.0),
        "state_1B_substantively_used": state_1b_access.get("whether_1B_budget_was_substantively_used", False),
        "candidate_miss_rate_100M": reference["candidate_miss_rate"],
        "candidate_miss_rate_1B": state_1b_row.get("candidate_miss_rate", 0.0),
        "top1_100M": reference["top1_correct_rate"],
        "top1_1B": state_1b_row.get("top1_correct_rate", 0.0),
        "heldout_supported_success_rate_1B": state_1b_row.get("heldout_supported_success_rate", 0.0),
        "boundary_false_accept_rate_1B": state_1b_row.get("boundary_false_accept_rate", 0.0),
        "future_domain_supported_accept_rate_1B": state_1b_row.get("future_domain_supported_accept_rate", 0.0),
        "compiler_validation_completed": compiler.get("compiler_validation_completed", False),
        "compiler_verified_correct_rate_best": best_compiler.get("compiler_verified_correct_rate", 0.0),
        "boundary_compiler_misroute_count_best": best_compiler.get("boundary_compiler_misroute_count", 0),
        "capacity_threshold_signal_detected": scaling["capacity_threshold_signal_detected"],
        "sharp_transition_detected": scaling["sharp_transition_detected"],
        "smooth_scaling_detected": scaling["smooth_scaling_detected"],
        "diminishing_returns_detected": scaling["diminishing_returns_detected"],
        "saturation_detected": scaling["saturation_detected"],
        "memory_guard_passed": memory_guard_passed,
        "access_audit_completed": access["access_audit_completed"],
        "cross_process_reload_passed": cross_process_reload_passed,
        "ready_for_profile_promotion_probe": claim == "billion_state_budget_probe_positive" and cross_process_reload_passed,
        "recommended_claim_level": claim,
        "blocking_issues": blocking,
        "required_next_run": "profile promotion probe with access-aware 1B lazy-indexed constraints" if claim == "billion_state_budget_probe_positive" else "review upper-frontier cost/benefit and access saturation",
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "billion_state_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result

