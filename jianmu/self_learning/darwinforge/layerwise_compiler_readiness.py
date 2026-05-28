from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


STILL_NOT_PROVEN = [
    "Turing completeness",
    "solved arithmetic",
    "solved program synthesis",
    "stable convergence",
    "solved OOD",
    "general program synthesis",
    "same-size LLM advantage",
    "safe real promotion",
    "production readiness",
    "emergence proven",
    "profile promotion completed",
]


def build_layerwise_compiler_readiness(
    output_records: str | Path,
    taxonomy: Dict[str, Any],
    replay: Dict[str, Any],
    clean: Dict[str, Any],
    integrity: Dict[str, Any],
) -> Dict[str, Any]:
    out = Path(output_records)
    runs = clean.get("runs", {})
    primary = runs.get("primary_16", {})
    best_label = clean.get("best_run_label", "")
    best = runs.get(best_label, {})
    primary_clean = _is_clean(primary)
    fallback_clean = best_label.startswith("fallback_") and _is_clean(best)
    semantic_failure = taxonomy.get("candidate_error_dominant") or taxonomy.get("freeze_prune_error_dominant") or best.get("wrong_stdout_count", 0) or best.get("candidate_mapping_error_count", 0) or best.get("freeze_prune_transfer_error_count", 0)
    blocking: List[str] = []
    if not (primary_clean or fallback_clean):
        blocking.append("layerwise_clean_rerun_not_clean")
    if semantic_failure:
        blocking.append("candidate_or_freeze_prune_semantic_failure_detected")
    if not integrity.get("mandatory_counter_guard_passed", False):
        blocking.append("integrity_check_failed")
    if semantic_failure:
        claim = "candidate_or_freeze_prune_semantic_failure_detected"
    elif primary_clean:
        claim = "layerwise_compiler_validation_restored"
    elif fallback_clean:
        claim = "layerwise_compiler_validation_restored_with_fallback"
    elif taxonomy.get("environment_issue_suspected"):
        claim = "layerwise_environment_failure_confirmed_but_not_restored"
    else:
        claim = "failed"
    result = {
        "taxonomy_completed": taxonomy.get("taxonomy_completed", False),
        "failure_replay_completed": replay.get("failure_replay_completed", False),
        "clean_rerun_completed": clean.get("clean_rerun_completed", False),
        "primary_clean": primary_clean,
        "fallback_clean": fallback_clean,
        "original_failure_count": taxonomy.get("original_failure_count", 0),
        "classified_failure_count": taxonomy.get("classified_failure_count", 0),
        "unknown_failure_count": taxonomy.get("unknown_failure_count", 0),
        "dominant_failure_category": taxonomy.get("dominant_failure_category"),
        "engineering_issue_dominant": taxonomy.get("engineering_issue_dominant", False),
        "candidate_error_dominant": taxonomy.get("candidate_error_dominant", False),
        "freeze_prune_error_dominant": taxonomy.get("freeze_prune_error_dominant", False),
        "environment_issue_suspected": taxonomy.get("environment_issue_suspected", False),
        "primary_compiler_verified_correct_rate": primary.get("compiler_verified_correct_rate", 0.0),
        "fallback_compiler_verified_correct_rate": best.get("compiler_verified_correct_rate", 0.0) if best_label.startswith("fallback_") else 0.0,
        "best_clean_run_label": best_label,
        "best_compiler_verified_correct_rate": best.get("compiler_verified_correct_rate", 0.0),
        "permission_error_count_best": best.get("permission_error_count", 0),
        "cleanup_failure_count_best": best.get("cleanup_failure_count", 0),
        "wrong_stdout_count_best": best.get("wrong_stdout_count", 0),
        "candidate_mapping_error_count_best": best.get("candidate_mapping_error_count", 0),
        "freeze_prune_transfer_error_count_best": best.get("freeze_prune_transfer_error_count", 0),
        "boundary_compiler_misroute_count_best": best.get("boundary_compiler_misroute_count", 0),
        "future_domain_compiled_count_best": best.get("future_domain_compiled_count", 0),
        "recursion_compiled_count_best": best.get("recursion_compiled_count", 0),
        "array_compiled_count_best": best.get("array_compiled_count", 0),
        "function_compiled_count_best": best.get("function_compiled_count", 0),
        "original_result_preserved": integrity.get("original_v0_9_12_2_result_preserved", False),
        "layerwise_signal_supported_by_clean_compiler": primary_clean or fallback_clean,
        "ready_for_profile_promotion_probe": bool(primary_clean or fallback_clean) and not semantic_failure,
        "recommended_claim_level": claim,
        "blocking_issues": blocking,
        "required_next_run": "profile promotion probe with no real promotion" if (primary_clean or fallback_clean) and not semantic_failure else "compiler failure taxonomy follow-up or reduced-worker MSVC rerun before profile promotion probe",
    }
    _write_json(out / "layerwise_compiler_readiness.json", result)
    return result


def write_layerwise_compiler_mainline(output_records: str | Path, preflight: Dict[str, Any], taxonomy: Dict[str, Any], replay: Dict[str, Any], clean: Dict[str, Any], readiness: Dict[str, Any]) -> Dict[str, Any]:
    out = Path(output_records)
    conclusion = {
        "proven": [
            "v0.9.12.2 layerwise compiler failures were classified without overwriting original records",
            "clean MSVC rerun was reported separately from the original result",
        ],
        "not_proven": STILL_NOT_PROVEN,
        "v0_9_12_2_compiler_failure_main_cause": taxonomy.get("dominant_failure_category"),
        "security_or_environment_interference_evidence": {
            "known_360_process_detected": preflight.get("known_360_process_detected", False),
            "defender_or_security_lock_suspected": preflight.get("defender_or_security_lock_suspected", False),
            "environment_issue_suspected": taxonomy.get("environment_issue_suspected", False),
        },
        "candidate_program_semantic_failure_detected": readiness.get("candidate_error_dominant", False),
        "freeze_prune_transfer_semantic_failure_detected": readiness.get("freeze_prune_error_dominant", False),
        "failure_replay": replay,
        "clean_rerun": clean,
        "layerwise_compiler_validation_confidence_restored": readiness.get("layerwise_signal_supported_by_clean_compiler", False),
        "ready_for_profile_promotion_probe": readiness.get("ready_for_profile_promotion_probe", False),
        "recommended_claim_level": readiness.get("recommended_claim_level"),
        "blocking_issues": readiness.get("blocking_issues", []),
        "required_next_run": readiness.get("required_next_run"),
        "paper_v2_report_candidates": ["failure taxonomy", "clean rerun metrics", "environment/process lifecycle notes"],
        "v1_0_route_preserved": ["root similarity incremental training", "verified backend as teacher for NL-to-semantic-IR adapter"],
        "still_not_proven": STILL_NOT_PROVEN,
    }
    _write_json(out / "mainline_conclusion.json", conclusion)
    (out / "mainline_conclusion.md").write_text(_render_conclusion_md(conclusion), encoding="utf-8")
    return conclusion


def _is_clean(metrics: Dict[str, Any]) -> bool:
    return (
        metrics.get("completed")
        and metrics.get("compiler_verified_correct_rate", 0.0) >= 0.98
        and metrics.get("permission_error_count", 0) == 0
        and metrics.get("cleanup_failure_count", 0) == 0
        and metrics.get("boundary_compiler_misroute_count", 0) == 0
        and metrics.get("future_domain_compiled_count", 0) == 0
        and metrics.get("recursion_compiled_count", 0) == 0
        and metrics.get("array_compiled_count", 0) == 0
        and metrics.get("function_compiled_count", 0) == 0
        and metrics.get("backend_claim_safe")
    )


def _render_conclusion_md(result: Dict[str, Any]) -> str:
    lines = ["# v0.9.12.3 Mainline Conclusion", ""]
    for key in ["v0_9_12_2_compiler_failure_main_cause", "layerwise_compiler_validation_confidence_restored", "ready_for_profile_promotion_probe", "recommended_claim_level", "required_next_run"]:
        lines.append(f"- {key}: {result.get(key)}")
    lines.append("")
    lines.append("## Still Not Proven")
    for item in STILL_NOT_PROVEN:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
