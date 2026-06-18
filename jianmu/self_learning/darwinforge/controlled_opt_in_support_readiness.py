from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.controlled_opt_in_support_schema import STILL_NOT_PROVEN


def build_controlled_opt_in_support_readiness(
    output_records: str | Path,
    scope: Dict[str, Any],
    unsupported: Dict[str, Any],
    taxonomy: Dict[str, Any],
    negative: Dict[str, Any],
    positive: Dict[str, Any],
    rollback: Dict[str, Any],
    trace_pack: Dict[str, Any],
    reviewer_pack: Dict[str, Any],
    workers_requested: int = 16,
    workers_used: int = 16,
) -> Dict[str, Any]:
    negative_clean = negative.get("negative_validation_passed") is True
    positive_clean = positive.get("positive_validation_passed") is True
    safety_clean = (
        rollback.get("default_profile_unchanged") is True
        and rollback.get("explicit_opt_in_required") is True
        and not rollback.get("default_profile_bridge_leak_detected")
        and not rollback.get("real_promotion_enabled")
        and not rollback.get("user_facing_enabled")
        and not rollback.get("official_release_enabled")
        and rollback.get("opt_in_rollback_passed") is True
        and rollback.get("regression_guard_passed") is True
    )
    production_flags_false = True
    if negative_clean and positive_clean and safety_clean and trace_pack.get("trace_pack_replayable") and reviewer_pack.get("reviewer_support_pack_generated") and production_flags_false:
        level = "controlled_opt_in_support_candidate_ready"
    elif not negative_clean:
        level = "controlled_support_blocked_by_negative_boundary"
    elif not positive_clean:
        level = "controlled_support_blocked_by_positive_validation"
    elif rollback.get("default_profile_bridge_leak_detected"):
        level = "controlled_support_blocked_by_default_leak"
    else:
        level = "failed"
    blocking = []
    if not negative_clean:
        blocking.append("negative_boundary_not_clean")
    if not positive_clean:
        blocking.append("positive_validation_not_clean")
    if not safety_clean:
        blocking.append("default_rollback_regression_not_clean")
    result = {
        "controlled_support_review_started": True,
        "controlled_support_review_completed": True,
        "no_model_training": True,
        "no_weight_update": True,
        "reused_existing_logic": True,
        "staged_opt_in_enabled": True,
        **scope,
        **unsupported,
        **taxonomy,
        **negative,
        **positive,
        **rollback,
        **trace_pack,
        **reviewer_pack,
        "workers_requested": workers_requested,
        "workers_used": workers_used,
        "downgrade_reason": "",
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "controlled_opt_in_support_candidate_ready": level == "controlled_opt_in_support_candidate_ready",
        "ready_for_official_release": False,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "controlled opt-in support candidate human review; do not claim production support completed",
        "still_not_proven": list(STILL_NOT_PROVEN),
    }
    result.pop("rows", None)
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "controlled_opt_in_support_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
