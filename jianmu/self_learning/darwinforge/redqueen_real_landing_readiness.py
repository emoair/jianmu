from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_real_landing_schema import STILL_NOT_PROVEN_REAL_LANDING


def build_real_landing_readiness(
    output_records: str | Path,
    summary: Dict[str, Any],
) -> Dict[str, Any]:
    blocking = []
    if not summary.get("endurance_lifecycle_guard_passed"):
        blocking.append("lifecycle_guard_failed")
        level = "redqueen_real_landing_blocked_by_lifecycle"
    elif not summary.get("distribution_effect_audit_passed"):
        blocking.append("distribution_effect_failed")
        level = "redqueen_real_landing_blocked_by_distribution"
    elif not summary.get("governance_safety_audit_passed"):
        blocking.append("governance_drift_detected")
        level = "redqueen_real_landing_blocked_by_governance_drift"
    elif summary.get("compiler_verified_correctness_rate") != 1.0 or summary.get("wrong_stdout_count", 0) != 0:
        blocking.append("compile_correctness_failed")
        level = "redqueen_real_landing_blocked_by_compile_correctness"
    elif not summary.get("frontier_pressure_audit_passed"):
        level = "redqueen_real_landing_positive_with_frontier_notes"
    elif all([
        summary.get("wall_clock_hours", 0) >= 6,
        summary.get("cycles_completed") == 3,
        summary.get("total_events", 0) >= 120_000,
        summary.get("real_compiler_invocations", 0) >= 90_000,
        summary.get("plan_follow_rate_mean", 0) >= 0.95,
        summary.get("redqueen_controlled_distribution"),
        summary.get("adaptive_curriculum_applied"),
        summary.get("no_fake_weak_category_detected"),
        summary.get("frontier_pressure_audit_passed"),
        summary.get("default_profile_unchanged"),
        not summary.get("real_promotion_enabled"),
    ]):
        level = "redqueen_real_landing_endurance_positive"
    else:
        blocking.append("endurance_threshold_not_met")
        level = "failed"
    result = {
        **summary,
        "redqueen_real_landing_endurance_positive": level == "redqueen_real_landing_endurance_positive",
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "RedQueen multi-round governance validation; do not claim production support completed",
        "still_not_proven": list(STILL_NOT_PROVEN_REAL_LANDING),
    }
    _write_json(Path(output_records) / "redqueen_real_landing_readiness.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
