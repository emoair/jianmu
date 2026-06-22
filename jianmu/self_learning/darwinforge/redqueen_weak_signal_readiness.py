from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_weak_signal_schema import STILL_NOT_PROVEN_WEAK_SIGNAL


def build_weak_signal_readiness(output_records: str | Path, summary: Dict[str, Any]) -> Dict[str, Any]:
    blocking = []
    level = "failed"
    if not summary.get("synthetic_signal_honesty_audit_passed"):
        blocking.append("honesty_audit_failed")
        level = "redqueen_weak_signal_blocked_by_honesty_audit"
    elif not summary.get("real_compile_lane_passed"):
        blocking.append("real_compile_lane_failed")
        level = "redqueen_weak_signal_blocked_by_real_compile_lane"
    elif not summary.get("distribution_response_audit_passed"):
        blocking.append("distribution_response_failed")
        level = "redqueen_weak_signal_blocked_by_distribution_response"
    elif not summary.get("multiround_lifecycle_guard_passed"):
        blocking.append("lifecycle_guard_failed")
        level = "redqueen_weak_signal_blocked_by_lifecycle"
    elif not summary.get("governance_safety_audit_passed"):
        blocking.append("governance_drift_detected")
        level = "redqueen_weak_signal_blocked_by_governance_drift"
    elif _positive(summary):
        level = "redqueen_controlled_weak_signal_response_positive"
    elif summary.get("compiler_verified_correctness_rate") == 1.0 and summary.get("weak_signal_injected"):
        level = "redqueen_weak_signal_positive_with_notes"
    else:
        blocking.append("weak_signal_threshold_not_met")
    result = {
        **summary,
        "redqueen_controlled_weak_signal_response_positive": level == "redqueen_controlled_weak_signal_response_positive",
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "RedQueen multi-round governance stability validation; do not claim production support completed",
        "still_not_proven": list(STILL_NOT_PROVEN_WEAK_SIGNAL),
    }
    _write_json(Path(output_records) / "redqueen_weak_signal_readiness.json", result)
    return result


def _positive(summary: Dict[str, Any]) -> bool:
    return all([
        summary.get("wall_clock_hours", 0) >= 6,
        summary.get("cycles_completed", 0) >= 5,
        summary.get("total_events", 0) >= 130_000,
        summary.get("real_compiler_invocations", 0) >= 90_000,
        summary.get("real_compile_lane_passed"),
        summary.get("compiler_verified_correctness_rate") == 1.0,
        summary.get("weak_signal_is_synthetic"),
        not summary.get("weak_signal_affected_real_correctness"),
        summary.get("function_weak_signal_response_passed"),
        summary.get("mixed_weak_signal_response_passed"),
        summary.get("stable_recursion_annealing_passed"),
        summary.get("recovery_annealing_audit_passed"),
        summary.get("synthetic_signal_honesty_audit_passed"),
        summary.get("distribution_response_audit_passed"),
        summary.get("multiround_lifecycle_guard_passed"),
        summary.get("governance_safety_audit_passed"),
        summary.get("default_profile_unchanged"),
        not summary.get("real_promotion_enabled"),
        not summary.get("production_function_support_completed"),
        not summary.get("production_array_support_completed"),
        not summary.get("production_recursion_support_completed"),
    ])


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
