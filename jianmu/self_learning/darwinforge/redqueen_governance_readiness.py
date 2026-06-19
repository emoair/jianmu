from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.architecture_finalization_schema import STILL_NOT_PROVEN


def build_redqueen_governance_readiness(
    output_records: str | Path,
    architecture: Dict[str, Any],
    alignment: Dict[str, Any],
    metrics: Dict[str, Any],
    allocation: Dict[str, Any],
    schedule: Dict[str, Any],
    policy: Dict[str, Any],
    dry_run: Dict[str, Any],
    next_plan: Dict[str, Any],
) -> Dict[str, Any]:
    blockers = []
    if not architecture.get("architecture_finalization_passed"):
        blockers.append("architecture_finalization_failed")
        level = "redqueen_blocked_by_architecture_finalization"
    elif not alignment.get("support_scope_codepath_aligned"):
        blockers.append("support_scope_alignment_failed")
        level = "redqueen_blocked_by_scope_alignment"
    elif not policy.get("self_governance_policy_passed"):
        blockers.append("governance_policy_failed")
        level = "redqueen_blocked_by_governance_policy"
    elif not dry_run.get("redqueen_dry_run_passed"):
        blockers.append("dry_run_failed")
        level = "redqueen_blocked_by_dry_run"
    else:
        level = "redqueen_governance_bootstrap_ready"
    result = {
        **architecture,
        **alignment,
        **metrics,
        **allocation,
        **schedule,
        **policy,
        **dry_run,
        **next_plan,
        "redqueen_governance_bootstrap_started": True,
        "redqueen_governance_bootstrap_completed": level == "redqueen_governance_bootstrap_ready",
        "no_model_training": True,
        "no_weight_update": True,
        "reused_existing_logic": True,
        "default_profile_unchanged": True,
        "explicit_opt_in_required": True,
        "staged_opt_in_enabled": True,
        "real_promotion_enabled": False,
        "user_facing_enabled": False,
        "official_release_enabled": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "controlled_opt_in_support_approved": False,
        "redqueen_governance_bootstrap_ready": level == "redqueen_governance_bootstrap_ready",
        "ready_for_official_release": False,
        "recommended_claim_level": level,
        "blocking_issues": blockers,
        "required_next_run": "RedQueen governance iteration or human signoff; do not claim production support completed",
        "still_not_proven": list(STILL_NOT_PROVEN),
    }
    path = Path(output_records) / "redqueen_governance_readiness.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
