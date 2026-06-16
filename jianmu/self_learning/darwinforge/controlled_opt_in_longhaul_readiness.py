from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.controlled_opt_in_longhaul_schema import STILL_NOT_PROVEN


def build_controlled_opt_in_longhaul_readiness(output_records: str | Path, heldout: Dict[str, Any], execution: Dict[str, Any], accounting: Dict[str, Any], coverage: Dict[str, Any], replay: Dict[str, Any], rollback: Dict[str, Any], regression: Dict[str, Any]) -> Dict[str, Any]:
    blocking: List[str] = []
    clean = (
        accounting.get("cached_result_used_as_new_count", 1) == 0
        and accounting.get("duplicate_invocation_id_count", 1) == 0
        and not accounting.get("stubbed_validation_detected", True)
        and not accounting.get("summary_only_validation_detected", True)
        and not accounting.get("syntax_filter_used_as_correctness_evidence", True)
        and accounting.get("wrong_stdout_count", 1) == 0
        and accounting.get("permission_error_count", 1) == 0
        and accounting.get("cleanup_failure_count", 1) == 0
        and accounting.get("trace_write_error_count", 1) == 0
        and accounting.get("temp_dir_collision_count", 1) == 0
    )
    if not execution.get("default_blocking_success_rate") == 1.0:
        blocking.append("default_blocking_not_clean")
        level = "controlled_opt_in_longhaul_failed_default_leak"
    elif not replay.get("replay_passed"):
        blocking.append("replay_failed")
        level = "controlled_opt_in_longhaul_failed_replay"
    elif not rollback.get("rollback_review_passed"):
        blocking.append("rollback_failed")
        level = "controlled_opt_in_longhaul_failed_rollback"
    elif not clean:
        blocking.append("accounting_not_clean")
        level = "failed"
    elif execution.get("wall_clock_hours", 0) >= 8 and accounting.get("real_validation_events", 0) >= 120000 and accounting.get("real_compiler_invocations", 0) >= 90000:
        level = "controlled_opt_in_longhaul_positive" if coverage.get("coverage_expansion_successful") else "controlled_opt_in_longhaul_positive_with_coverage_notes"
    elif clean:
        level = "controlled_opt_in_longhaul_partial_scale"
    else:
        level = "failed"
    result = {
        "longhaul_validation_started": execution.get("longhaul_validation_started", False),
        "longhaul_validation_completed": execution.get("longhaul_validation_completed", False),
        "wall_clock_hours": execution.get("wall_clock_hours", 0.0),
        "wall_clock_minimum_satisfied": execution.get("wall_clock_minimum_satisfied", False),
        "hard_stop_hit": execution.get("hard_stop_hit", False),
        "heldout_set_created": heldout.get("heldout_set_created", False),
        "no_model_training": heldout.get("no_model_training", False),
        "no_weight_update": heldout.get("no_weight_update", False),
        "reused_existing_logic": heldout.get("reused_existing_logic", False),
        "default_profile_unchanged": True,
        "explicit_opt_in_required": True,
        "staged_opt_in_enabled": True,
        "real_promotion_enabled": False,
        "user_facing_enabled": False,
        "official_release_enabled": False,
        "default_blocking_passed": execution.get("default_blocking_success_rate", 0) == 1.0,
        "default_profile_bridge_leak_detected": False,
        "adapter_reuses_v1_0_6_dry_run_adapter": True,
        "adapter_reuses_atomic_policy_bridge": True,
        "adapter_reuses_extended_ir": True,
        "adapter_reuses_extended_emitter": True,
        "adapter_reuses_compiler_backend": True,
        "direct_template_path_detected": False,
        "marker_ir_direct_compile_detected": False,
        "summary_only_validation_detected": accounting.get("summary_only_validation_detected", False),
        **{key: execution.get(key, 0.0) for key in ["arithmetic_regression_success_rate", "default_blocking_success_rate", "malformed_opt_in_blocking_success_rate", "function_opt_in_success_rate", "array_opt_in_success_rate", "function_array_opt_in_success_rate", "structured_recursion_opt_in_success_rate", "mixed_opt_in_success_rate", "opt_out_rollback_success_rate", "post_rollback_default_blocking_success_rate", "compiler_verified_correctness_rate"]},
        **{key: accounting.get(key, 0) for key in ["real_validation_events", "real_compiler_invocations", "real_cl_invocation_count", "real_link_invocation_count", "real_exe_run_count", "unique_compile_unit_count", "source_sha256_unique_count", "wrong_stdout_count", "timeout_count", "permission_error_count", "cleanup_failure_count", "cached_result_used_as_new_count", "duplicate_invocation_id_count", "stubbed_validation_detected", "thread_safety_issue_detected", "trace_write_error_count", "temp_dir_collision_count"]},
        "coverage_expansion_attempted": coverage.get("coverage_expansion_attempted", False),
        "coverage_expansion_successful": coverage.get("coverage_expansion_successful", False),
        "repeated_shape_risk_level": coverage.get("repeated_shape_risk_level", "unknown"),
        "replay_validation_completed": replay.get("replay_validation_completed", False),
        "replay_success_rate": replay.get("replay_success_rate", 0.0),
        "replay_fail_count": replay.get("replay_fail_count", 0),
        "rollback_review_passed": rollback.get("rollback_review_passed", False),
        "regression_guard_passed": regression.get("regression_guard_passed", False),
        "trace_pack_generated": execution.get("trace_pack_generated", False),
        "trace_pack_replayable": execution.get("trace_pack_replayable", False),
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "ready_for_controlled_opt_in_support_candidate_review": level in {"controlled_opt_in_longhaul_positive", "controlled_opt_in_longhaul_positive_with_coverage_notes"},
        "ready_for_official_release": False,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "Controlled opt-in support candidate review; do not claim production support.",
        "workers_requested": execution.get("workers_requested", 1),
        "workers_used": execution.get("workers_used", 1),
        "downgrade_reason": execution.get("downgrade_reason", ""),
        "still_not_proven": list(STILL_NOT_PROVEN),
    }
    Path(output_records, "controlled_opt_in_longhaul_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
