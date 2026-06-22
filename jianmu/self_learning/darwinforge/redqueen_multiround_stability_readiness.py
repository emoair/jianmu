from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_multiround_stability_schema import STILL_NOT_PROVEN_STABILITY


def build_stability_readiness(output_records: str | Path, summary: Dict[str, Any]) -> Dict[str, Any]:
    blocking = []
    if not summary.get("msvc_preflight_passed"):
        blocking.append("msvc_environment_not_ready")
        level = "msvc_environment_not_ready"
    elif not summary.get("stability_drift_audit_passed"):
        blocking.append("stability_drift_failed")
        level = "redqueen_stability_blocked_by_drift"
    elif not summary.get("response_stability_audit_passed"):
        blocking.append("response_stability_failed")
        level = "redqueen_stability_blocked_by_response_instability"
    elif not summary.get("multiround_lifecycle_guard_passed"):
        blocking.append("lifecycle_guard_failed")
        level = "redqueen_stability_blocked_by_lifecycle"
    elif not summary.get("real_compile_lane_passed"):
        blocking.append("real_compile_lane_failed")
        level = "redqueen_stability_blocked_by_real_compile_lane"
    elif _positive(summary):
        level = "redqueen_multiround_stability_positive"
    elif summary.get("compiler_verified_correctness_rate") == 1.0 and summary.get("msvc_preflight_passed"):
        level = "redqueen_stability_positive_with_env_notes"
    else:
        blocking.append("stability_threshold_not_met")
        level = "failed"
    result = {
        **summary,
        "redqueen_multiround_stability_positive": level == "redqueen_multiround_stability_positive",
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "RedQueen long-run governance stability or human signoff; do not claim production support completed",
        "still_not_proven": list(STILL_NOT_PROVEN_STABILITY),
    }
    _write_json(Path(output_records) / "redqueen_multiround_stability_readiness.json", result)
    return result


def _positive(summary: Dict[str, Any]) -> bool:
    return all([
        summary.get("msvc_preflight_passed"),
        summary.get("msvc_fail_fast_test_passed"),
        summary.get("wall_clock_hours", 0) >= 8,
        summary.get("cycles_completed", 0) >= 8,
        summary.get("total_events", 0) >= 180_000,
        summary.get("real_compiler_invocations", 0) >= 130_000,
        summary.get("real_compile_lane_passed"),
        summary.get("compiler_verified_correctness_rate") == 1.0,
        summary.get("stability_drift_audit_passed"),
        summary.get("response_stability_audit_passed"),
        summary.get("perturbation_recovery_audit_passed"),
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
