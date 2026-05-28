from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def build_state_budget_readiness(
    output_records: str | Path,
    profiles_attempted: List[str],
    profiles_completed: List[str],
    profiles_skipped: Dict[str, str],
    best: Dict[str, Any],
    baseline: Dict[str, Any],
    scaling: Dict[str, Any],
    compiler: Dict[str, Any],
    integrity: Dict[str, Any],
    memory_guard_passed: bool,
    cross_process_reload_passed: bool,
) -> Dict[str, Any]:
    best_compiler = compiler.get("per_profile", {}).get(best["profile_name"], {})
    blocking = []
    if integrity.get("forbidden_field_access_count", 0):
        blocking.append("forbidden_field_access")
    if best_compiler.get("compiler_verified_correct_rate", 0.0) < 0.98:
        blocking.append("compiler_validation_low")
    if best_compiler.get("boundary_compiler_misroute_count", 0):
        blocking.append("boundary_compiler_misroute")
    if best.get("future_domain_supported_accept_rate", 0.0) != 0.0:
        blocking.append("future_domain_false_accept")
    hundred_completed = "state_100M" in profiles_completed
    positive = best["candidate_miss_rate"] < baseline["candidate_miss_rate"] and best["top1_correct_rate"] > baseline["top1_correct_rate"]
    if not blocking and hundred_completed and positive and memory_guard_passed:
        claim = "hundred_million_state_budget_probe_positive"
    elif not blocking and positive:
        claim = "state_budget_scale_positive_below_100M"
    elif positive:
        claim = "state_budget_scale_mixed"
    else:
        claim = "state_budget_scale_not_reproduced"
    result = {
        "state_budget_probe_completed": bool(profiles_completed),
        "profiles_attempted": profiles_attempted,
        "profiles_completed": profiles_completed,
        "profiles_skipped": profiles_skipped,
        "best_profile_name": best["profile_name"],
        "best_target_state_units": best["target_state_units"],
        "best_actual_state_units_allocated": best["actual_state_units_allocated"],
        "best_materialization_level": best["materialization_level"],
        "candidate_miss_rate_baseline": baseline["candidate_miss_rate"],
        "candidate_miss_rate_best": best["candidate_miss_rate"],
        "top1_baseline": baseline["top1_correct_rate"],
        "top1_best": best["top1_correct_rate"],
        "heldout_supported_success_rate_best": best["heldout_supported_success_rate"],
        "boundary_false_accept_rate_best": best["boundary_false_accept_rate"],
        "future_domain_supported_accept_rate_best": best["future_domain_supported_accept_rate"],
        "compiler_validation_completed": compiler.get("compiler_validation_completed", False),
        "compiler_verified_correct_rate_best": best_compiler.get("compiler_verified_correct_rate", 0.0),
        "boundary_compiler_misroute_count_best": best_compiler.get("boundary_compiler_misroute_count", 0),
        "capacity_threshold_signal_detected": scaling["capacity_threshold_signal_detected"],
        "sharp_transition_detected": scaling["sharp_transition_detected"],
        "diminishing_returns_detected": scaling["diminishing_returns_detected"],
        "memory_guard_passed": memory_guard_passed,
        "cross_process_reload_passed": cross_process_reload_passed,
        "ready_for_v0_9_12_training_or_profile_promotion": claim in {"hundred_million_state_budget_probe_positive", "state_budget_scale_positive_below_100M"} and cross_process_reload_passed,
        "recommended_claim_level": claim,
        "blocking_issues": blocking,
        "required_next_run": "v0.9.12 training/profile-promotion probe with honest materialization constraints" if not blocking else "resolve compiler/integrity blockers",
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "state_budget_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result

