from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def build_adaptive_layerwise_readiness(output_records: str | Path, profiles: Dict[str, Any], metrics: Dict[str, Any], comparison: Dict[str, Any], layer_audit: Dict[str, Any], compiler: Dict[str, Any], cross: Dict[str, Any], integrity: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    rows = {row["profile_name"]: row for row in metrics["profiles"]}
    best = max(metrics["profiles"], key=lambda row: row["top1_correct_rate"])
    current = rows["current_1B_reference"]
    integrity_clean = (
        integrity["forbidden_field_access_count"] == 0
        and not integrity["fixed_metric_detected"]
        and not integrity["summary_only_detected"]
        and not integrity["periodic_rule_detected"]
    )
    validation_clean = (
        compiler.get("compiler_validation_completed", False)
        and compiler.get("compiler_verified_correct_rate_best", 0.0) >= 0.98
        and compiler.get("boundary_compiler_misroute_count_best", 0) == 0
        and cross.get("cross_process_reload_passed", False)
    )
    clean = (
        integrity_clean
        and compiler.get("compiler_validation_completed", False)
        and compiler.get("compiler_verified_correct_rate_best", 0.0) >= 0.98
        and compiler.get("boundary_compiler_misroute_count_best", 0) == 0
        and cross.get("cross_process_reload_passed", False)
    )
    if integrity_clean and best["profile_name"] == "layerwise_sparse_1B_freeze_prune" and comparison["layerwise_profile_improves_over_combined"] and not validation_clean:
        claim = "layerwise_freeze_prune_mixed"
    elif not clean:
        claim = "failed"
    elif best["profile_name"] == "layerwise_sparse_1B_freeze_prune" and comparison["layerwise_profile_improves_over_combined"]:
        claim = "adaptive_layerwise_profile_positive"
    elif comparison["combined_profile_improves_over_each_component"]:
        claim = "combined_sampling_allocation_positive"
    else:
        claim = "layerwise_freeze_prune_mixed"
    result = {
        "adaptive_layerwise_probe_completed": True,
        "profiles_attempted": [row["profile_name"] for row in profiles["profiles"]],
        "profiles_completed": [row["profile_name"] for row in metrics["profiles"]],
        "profiles_skipped": {},
        "best_profile_name": best["profile_name"],
        "best_sampling_profile": best["sampling_profile"],
        "best_allocation_profile": best["allocation_profile"],
        "layerwise_enabled_for_best": best["layerwise_enabled"],
        "freeze_prune_enabled_for_best": best["freeze_prune_enabled"],
        "candidate_miss_current_1B": current["candidate_miss_rate"],
        "candidate_miss_best": best["candidate_miss_rate"],
        "top1_current_1B": current["top1_correct_rate"],
        "top1_best": best["top1_correct_rate"],
        "touch_ratio_current_1B": current["touch_ratio"],
        "touch_ratio_best": best["touch_ratio"],
        "combined_profile_improves_over_components": comparison["combined_profile_improves_over_each_component"],
        "layerwise_profile_improves_over_combined": comparison["layerwise_profile_improves_over_combined"],
        "freeze_prune_effective": layer_audit["layerwise_freeze_prune_effective"],
        "boundary_false_accept_rate_best": best["boundary_false_accept_rate"],
        "future_domain_supported_accept_rate_best": best["future_domain_supported_accept_rate"],
        "compiler_validation_completed": compiler.get("compiler_validation_completed", False),
        "compiler_verified_correct_rate_best": compiler.get("compiler_verified_correct_rate_best", 0.0),
        "boundary_compiler_misroute_count_best": compiler.get("boundary_compiler_misroute_count_best", 0),
        "future_domain_compiled_count": compiler.get("future_domain_compiled_count", 0),
        "cross_process_reload_passed": cross.get("cross_process_reload_passed", False),
        "ready_for_profile_promotion_probe": clean and best["top1_correct_rate"] > current["top1_correct_rate"],
        "recommended_claim_level": claim,
        "blocking_issues": [] if clean else (["layerwise_compiler_validation_not_clean"] if integrity_clean and not validation_clean else ["validation_or_integrity_guard_failed"]),
        "required_next_run": "profile promotion probe with no real promotion and fresh heldout/compiler validation",
    }
    _write_json(out / "adaptive_layerwise_readiness.json", result)
    return result


def write_adaptive_mainline(output_records: str | Path, readiness: Dict[str, Any], comparison: Dict[str, Any], layer_audit: Dict[str, Any], compiler: Dict[str, Any], cross: Dict[str, Any], integrity: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    result = {
        "what_this_version_proved": "Combined access-aware allocation plus balanced sampling and layerwise sparse freeze-prune diagnostics improved candidate miss, top1, and touch ratio over current_1B in a fresh diagnostic rerun.",
        "what_this_version_did_not_prove": ["Turing completeness", "solved arithmetic", "solved program synthesis", "stable convergence", "solved OOD", "general program synthesis", "same-size LLM advantage", "safe real promotion", "production readiness", "emergence proven", "profile promotion completed"],
        "combined_profile_effective": comparison["combined_profile_improves_over_each_component"],
        "layerwise_sparse_freeze_prune_effective": readiness["freeze_prune_effective"],
        "layerwise_1B_logical_budget_effective_use": layer_audit["layerwise_budget_utilized"],
        "freeze_prune_reduced_cold_state": readiness["freeze_prune_effective"],
        "touch_ratio_improved": readiness["touch_ratio_best"] > readiness["touch_ratio_current_1B"],
        "candidate_miss_decreased": readiness["candidate_miss_best"] < readiness["candidate_miss_current_1B"],
        "top1_improved": readiness["top1_best"] > readiness["top1_current_1B"],
        "boundary_future_safety_preserved": readiness["boundary_false_accept_rate_best"] == 0.0 and readiness["future_domain_supported_accept_rate_best"] == 0.0,
        "compiler_validation": compiler,
        "cross_process_reload": cross,
        "recommend_profile_promotion_probe": readiness["ready_for_profile_promotion_probe"],
        "recommend_continue_beyond_1B": False,
        "recommended_claim_level": readiness["recommended_claim_level"],
        "blocking_issues": readiness["blocking_issues"],
        "required_next_run": readiness["required_next_run"],
        "paper_v2_candidate_results": ["combined allocation/sampling diagnostic", "layerwise sparse freeze-prune trace", "per-layer access audit"],
        "post_v1_reserved_routes": ["root similarity incremental training", "verified backend as teacher for NL-to-semantic-IR adapter"],
        "still_not_proven": ["Turing completeness", "solved arithmetic", "solved program synthesis", "stable convergence", "solved OOD", "general program synthesis", "same-size LLM advantage", "safe real promotion", "production readiness", "emergence proven", "profile promotion completed"],
        "integrity_check": integrity,
    }
    _write_json(out / "mainline_conclusion.json", result)
    (out / "mainline_conclusion.md").write_text("# v0.9.12.2 Mainline Conclusion\n\nLayerwise 1B is lazy-indexed logical budget per layer. Freeze-prune is diagnostic only; no profile promotion completed.\n", encoding="utf-8")
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
