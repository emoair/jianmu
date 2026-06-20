from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.redqueen_iteration_schema import STILL_NOT_PROVEN_ITERATION


def build_redqueen_iteration_readiness(
    output_records: str | Path,
    plan_loader: Dict[str, Any],
    pre_metrics: Dict[str, Any],
    execution: Dict[str, Any],
    post_metrics: Dict[str, Any],
    delta: Dict[str, Any],
    drift: Dict[str, Any],
    reaction: Dict[str, Any],
    next_plan: Dict[str, Any],
) -> Dict[str, Any]:
    blocking = []
    if not plan_loader.get("plan_loader_passed"):
        blocking.append("missing_or_invalid_source_plan")
        level = "redqueen_iteration_blocked_missing_plan"
    elif not execution.get("plan_execution_passed"):
        blocking.append("plan_execution_failed")
        level = "redqueen_iteration_blocked_plan_execution"
    elif not drift.get("governance_drift_audit_passed"):
        blocking.append("governance_drift_detected")
        level = "redqueen_iteration_blocked_governance_drift"
    elif reaction.get("overreaction_detected"):
        blocking.append("overreaction_detected")
        level = "redqueen_iteration_blocked_overreaction"
    elif reaction.get("underreaction_detected"):
        blocking.append("underreaction_detected")
        level = "redqueen_iteration_blocked_underreaction"
    elif not delta.get("metric_delta_review_passed"):
        blocking.append("metric_delta_review_failed")
        level = "redqueen_iteration_positive_with_notes"
    elif not next_plan.get("next_plan_v2_generated"):
        blocking.append("next_plan_v2_missing")
        level = "failed"
    else:
        level = "redqueen_governance_iteration_1_positive"
    result = {
        "redqueen_iteration_started": True,
        "redqueen_iteration_completed": level == "redqueen_governance_iteration_1_positive",
        "source_plan_loaded": plan_loader.get("source_plan_loaded", False),
        "pre_metrics_snapshot_created": pre_metrics.get("pre_metrics_snapshot_created", False),
        "plan_execution_completed": execution.get("plan_execution_completed", False),
        "post_metrics_snapshot_created": post_metrics.get("post_metrics_snapshot_created", False),
        "metric_delta_review_completed": delta.get("metric_delta_review_completed", False),
        "governance_drift_audit_passed": drift.get("governance_drift_audit_passed", False),
        "over_under_reaction_audit_passed": reaction.get("over_under_reaction_audit_passed", False),
        "next_plan_v2_generated": next_plan.get("next_plan_v2_generated", False),
        "iteration_events": execution.get("iteration_events", 0),
        "real_compiler_invocations": execution.get("real_compiler_invocations", 0),
        "plan_follow_rate": execution.get("plan_follow_rate", 0.0),
        "weak_category_received_more_review": delta.get("weak_category_received_more_review", False),
        "stable_category_annealed": delta.get("stable_category_annealed", False),
        "coverage_gap_category_received_shape_diversity": delta.get("coverage_gap_category_received_shape_diversity", False),
        "default_boundary_minimum_review_preserved": delta.get("default_boundary_minimum_review_preserved", False),
        "unsupported_boundary_minimum_review_preserved": delta.get("unsupported_boundary_minimum_review_preserved", False),
        "workers_requested": execution.get("workers_requested", 16),
        "workers_used": execution.get("workers_used", 16),
        "compiler_workers_requested": execution.get("compiler_workers_requested", 16),
        "compiler_workers_used": execution.get("compiler_workers_used", 16),
        "downgrade_reason": execution.get("downgrade_reason", ""),
        "no_model_training": True,
        "no_weight_update": True,
        "reused_existing_logic": True,
        "default_profile_unchanged": execution.get("default_profile_unchanged", False),
        "explicit_opt_in_required": True,
        "staged_opt_in_enabled": True,
        "real_promotion_enabled": execution.get("real_promotion_enabled", False),
        "user_facing_enabled": execution.get("user_facing_enabled", False),
        "official_release_enabled": execution.get("official_release_enabled", False),
        "direct_template_path_detected": drift.get("direct_template_path_detected", False),
        "marker_ir_direct_compile_detected": drift.get("marker_ir_direct_compile_detected", False),
        "summary_only_validation_detected": drift.get("summary_only_validation_detected", False),
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "redqueen_governance_iteration_1_positive": level == "redqueen_governance_iteration_1_positive",
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "RedQueen governance iteration 2 or multi-round stability validation; do not claim production support completed",
        "still_not_proven": list(STILL_NOT_PROVEN_ITERATION),
    }
    _write_json(Path(output_records) / "redqueen_iteration_readiness.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
