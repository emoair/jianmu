from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.mirror_redqueen_8h_schema import STILL_NOT_PROVEN_MIRROR_8H


def build_mirror_redqueen_8h_readiness(output_records: str | Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    blocking = []
    if not payload.get("preflight_truth_gate_passed"):
        blocking.append("truth_gate_failed")
        level = "mirror_redqueen_blocked_by_truth_gate"
    elif not payload.get("true_time_integrity_audit_passed"):
        blocking.append("time_integrity_failed")
        level = "mirror_redqueen_blocked_by_time_integrity"
    elif not payload.get("lane_swap_stability_audit_passed"):
        blocking.append("lane_swap_failed")
        level = "mirror_redqueen_blocked_by_lane_swap"
    elif not payload.get("frozen_lane_integrity_audit_passed"):
        blocking.append("frozen_lane_integrity_failed")
        level = "mirror_redqueen_blocked_by_frozen_lane_integrity"
    elif not payload.get("feedback_loop_audit_passed"):
        blocking.append("feedback_loop_failed")
        level = "mirror_redqueen_blocked_by_feedback_loop"
    elif not payload.get("lifecycle_guard_passed"):
        blocking.append("lifecycle_failed")
        level = "mirror_redqueen_blocked_by_lifecycle"
    elif _positive(payload):
        level = "mirror_redqueen_cosymbiosis_true_8h_positive"
    else:
        blocking.append("positive_threshold_not_met")
        level = "failed"
    result = {
        **payload,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "mirror_redqueen_cosymbiosis_true_8h_positive": level == "mirror_redqueen_cosymbiosis_true_8h_positive",
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
        "real_promotion_enabled": False,
        "default_profile_unchanged": True,
        "required_next_run": "Human review of v1.0.8.8 true 8h Mirror-RedQueen co-symbiosis evidence before any production-profile discussion.",
        "still_not_proven": list(STILL_NOT_PROVEN_MIRROR_8H),
    }
    _write_json(Path(output_records) / "mirror_redqueen_8h_readiness.json", result)
    return result


def _positive(payload: Dict[str, Any]) -> bool:
    return all([
        payload.get("actual_elapsed_seconds", 0) >= 28800,
        payload.get("cycles_completed") == 8,
        payload.get("total_events", 0) >= 160000,
        payload.get("real_compiler_invocations", 0) >= 110000,
        payload.get("compiler_verified_correctness_rate") == 1.0,
        payload.get("wrong_stdout_count", 0) == 0,
        payload.get("timeout_count", 0) == 0,
        payload.get("feedback_loop_audit_passed"),
        payload.get("distribution_audit_passed"),
        payload.get("over_under_reaction_audit_passed"),
        payload.get("real_compile_lane_passed"),
        payload.get("governance_safety_audit_passed"),
        payload.get("default_profile_unchanged"),
        not payload.get("real_promotion_enabled"),
        not payload.get("production_function_support_completed"),
        not payload.get("production_array_support_completed"),
        not payload.get("production_recursion_support_completed"),
    ])


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

