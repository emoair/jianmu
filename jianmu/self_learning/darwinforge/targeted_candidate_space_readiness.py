from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def build_targeted_readiness(
    output_records: str | Path,
    profile: Dict[str, Any],
    rerun: Dict[str, Any],
    compiler: Dict[str, Any],
    integrity: Dict[str, Any],
    cross_process_reload_passed: bool,
) -> Dict[str, Any]:
    blocking: list[str] = []
    if rerun.get("fresh_ratio", 0.0) < 0.90:
        blocking.append("fresh_ratio_below_0_90")
    if rerun.get("candidate_miss_rate_targeted", 1.0) >= rerun.get("candidate_miss_rate_baseline_reference", 0.0):
        blocking.append("candidate_miss_not_reduced")
    if compiler.get("compiler_verified_correct_rate", 0.0) < 0.98:
        blocking.append("compiler_validation_below_threshold")
    if compiler.get("boundary_compiler_misroute_count", 0):
        blocking.append("boundary_compiler_misroute")
    if compiler.get("future_domain_compiled_count", 0):
        blocking.append("future_domain_compiled")
    if integrity.get("forbidden_field_access_count", 0):
        blocking.append("forbidden_field_access")
    if profile.get("profile_is_architecture_change"):
        blocking.append("profile_marked_architecture_change")
    relief = rerun.get("candidate_miss_rate_targeted", 1.0) < rerun.get("candidate_miss_rate_baseline_reference", 0.0)
    claim = "targeted_candidate_space_expansion_reproduced" if not blocking and relief else "targeted_candidate_space_expansion_mixed"
    result = {
        "targeted_rerun_completed": not rerun.get("targeted_rerun_partial", False),
        "targeted_rerun_partial": rerun.get("targeted_rerun_partial", False),
        "partial_reason": rerun.get("partial_reason", ""),
        "profile_name": profile["profile_name"],
        "profile_is_architecture_change": profile["profile_is_architecture_change"],
        "fresh_ratio": rerun["fresh_ratio"],
        "candidate_miss_rate_baseline_reference": rerun["candidate_miss_rate_baseline_reference"],
        "candidate_miss_rate_targeted": rerun["candidate_miss_rate_targeted"],
        "candidate_miss_reduction": rerun["candidate_miss_reduction"],
        "correct_output_in_beam_targeted": rerun["correct_output_in_beam_targeted"],
        "top1_targeted": rerun["top1_targeted"],
        "top1_delta_vs_v0_9_8": rerun["top1_delta"],
        "boundary_false_accept_rate": rerun["boundary_false_accept_rate"],
        "future_domain_supported_accept_rate": rerun["future_domain_supported_accept_rate"],
        "compiler_validation_completed": compiler.get("compiler_validation_completed", False),
        "compiler_verified_correct_rate": compiler.get("compiler_verified_correct_rate", 0.0),
        "boundary_compiler_misroute_count": compiler.get("boundary_compiler_misroute_count", 0),
        "future_domain_compiled_count": compiler.get("future_domain_compiled_count", 0),
        "forbidden_field_access_count": integrity.get("forbidden_field_access_count", 0),
        "cross_process_reload_passed": cross_process_reload_passed,
        "generation_capacity_bottleneck_relief_confirmed": relief,
        "ready_for_state_budget_scale_probe": not blocking and relief and cross_process_reload_passed,
        "recommended_claim_level": claim if not blocking else "targeted_candidate_space_expansion_mixed",
        "blocking_issues": blocking,
        "required_next_run": "state-budget scale probe with the targeted candidate-space profile" if not blocking else "resolve blocking issues before scale probe",
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "targeted_candidate_space_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result

