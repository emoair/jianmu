from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.staged_opt_in_profile_schema import STILL_NOT_PROVEN


def build_staged_opt_in_readiness(
    output_records: str | Path,
    config: Dict[str, Any],
    guard: Dict[str, Any],
    blocking: Dict[str, Any],
    adapter: Dict[str, Any],
    execution: Dict[str, Any],
    rollback: Dict[str, Any],
    regression: Dict[str, Any],
) -> Dict[str, Any]:
    issues: List[str] = []
    clean_accounting = (
        execution.get("cached_result_used_as_new_count", 1) == 0
        and execution.get("duplicate_invocation_id_count", 1) == 0
        and not execution.get("stubbed_validation_detected", True)
        and not execution.get("summary_only_validation_detected", True)
        and not execution.get("syntax_filter_used_as_correctness_evidence", True)
        and execution.get("wrong_stdout_count", 1) == 0
        and execution.get("timeout_count", 1) == 0
        and execution.get("permission_error_count", 1) == 0
        and execution.get("cleanup_failure_count", 1) == 0
    )
    if not guard.get("staged_opt_in_guard_passed"):
        issues.append("staged_opt_in_guard_failed")
        level = "staged_opt_in_guard_failed"
    elif blocking.get("default_profile_bridge_leak_detected"):
        issues.append("default_profile_bridge_leak")
        level = "staged_opt_in_failed_default_leak"
    elif not regression.get("regression_guard_passed"):
        issues.append("regression_guard_failed")
        level = "staged_opt_in_regression_failed"
    elif not rollback.get("opt_in_rollback_passed"):
        issues.append("opt_in_rollback_failed")
        level = "staged_opt_in_rollback_failed"
    elif not clean_accounting:
        issues.append("compiler_accounting_not_clean")
        level = "failed"
    elif execution.get("wall_clock_hours", 0.0) >= 4 and execution.get("real_validation_events", 0) >= 45000 and execution.get("all_opt_in_categories_represented") and execution.get("trace_pack_replayable"):
        level = "staged_opt_in_profile_candidate_positive"
    elif clean_accounting:
        level = "staged_opt_in_positive_but_scale_partial"
    else:
        level = "failed"
    result = {
        "staged_opt_in_profile_created": config.get("staged_opt_in_profile_created", False),
        "staged_opt_in_profile_name": config.get("profile_name", ""),
        "default_profile_unchanged": config.get("default_profile_unchanged", False),
        "explicit_opt_in_required": config.get("opt_in_enabled_only_by_explicit_flag", False),
        "staged_opt_in_enabled": True,
        "staged_opt_in_executed": execution.get("staged_opt_in_executed", False),
        "real_promotion_enabled": config.get("real_promotion_enabled", True),
        "user_facing_enabled": config.get("user_facing_enabled", True),
        "official_release_enabled": config.get("official_release_enabled", True),
        "staged_opt_in_guard_passed": guard.get("staged_opt_in_guard_passed", False),
        "default_blocking_passed": blocking.get("default_blocking_passed", False),
        "default_profile_bridge_leak_detected": blocking.get("default_profile_bridge_leak_detected", True),
        "adapter_interface_valid": adapter.get("adapter_interface_valid", False),
        "adapter_reuses_v1_0_6_dry_run_adapter": adapter.get("adapter_reuses_v1_0_6_dry_run_adapter", False),
        "adapter_reuses_atomic_policy_bridge": adapter.get("adapter_reuses_atomic_policy_bridge", False),
        "adapter_reuses_extended_ir": adapter.get("adapter_reuses_extended_ir", False),
        "adapter_reuses_extended_emitter": adapter.get("adapter_reuses_extended_emitter", False),
        "adapter_reuses_compiler_backend": adapter.get("adapter_reuses_compiler_backend", False),
        "direct_template_path_detected": adapter.get("direct_template_path_detected", False),
        "marker_ir_direct_compile_detected": adapter.get("marker_ir_direct_compile_detected", False),
        "summary_only_validation_detected": adapter.get("summary_only_validation_detected", False) or execution.get("summary_only_validation_detected", False),
        "arithmetic_regression_compile_success_rate": execution.get("arithmetic_regression_compile_success_rate", 0.0),
        "function_opt_in_success_rate": execution.get("function_opt_in_success_rate", 0.0),
        "array_opt_in_success_rate": execution.get("array_opt_in_success_rate", 0.0),
        "function_array_opt_in_success_rate": execution.get("function_array_opt_in_success_rate", 0.0),
        "structured_recursion_opt_in_success_rate": execution.get("structured_recursion_opt_in_success_rate", 0.0),
        "mixed_opt_in_success_rate": execution.get("mixed_opt_in_success_rate", 0.0),
        "opt_out_rollback_success_rate": execution.get("opt_out_rollback_success_rate", 0.0),
        "wall_clock_hours": execution.get("wall_clock_hours", 0.0),
        "wall_clock_minimum_satisfied": execution.get("wall_clock_minimum_satisfied", False),
        "hard_stop_hit": execution.get("hard_stop_hit", False),
        "real_validation_events": execution.get("real_validation_events", 0),
        "real_compiler_invocations": execution.get("real_compiler_invocations", 0),
        "real_cl_invocation_count": execution.get("real_cl_invocation_count", 0),
        "real_link_invocation_count": execution.get("real_link_invocation_count", 0),
        "real_exe_run_count": execution.get("real_exe_run_count", 0),
        "unique_compile_unit_count": execution.get("unique_compile_unit_count", 0),
        "compiler_verified_correctness_rate": execution.get("compiler_verified_correctness_rate", 0.0),
        "wrong_stdout_count": execution.get("wrong_stdout_count", 0),
        "timeout_count": execution.get("timeout_count", 0),
        "permission_error_count": execution.get("permission_error_count", 0),
        "cleanup_failure_count": execution.get("cleanup_failure_count", 0),
        "cached_result_used_as_new_count": execution.get("cached_result_used_as_new_count", 0),
        "duplicate_invocation_id_count": execution.get("duplicate_invocation_id_count", 0),
        "stubbed_validation_detected": execution.get("stubbed_validation_detected", False),
        "regression_guard_passed": regression.get("regression_guard_passed", False),
        "opt_in_rollback_passed": rollback.get("opt_in_rollback_passed", False),
        "trace_pack_generated": execution.get("trace_pack_generated", False),
        "trace_pack_replayable": execution.get("trace_pack_replayable", False),
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "ready_for_controlled_opt_in_support_review": level == "staged_opt_in_profile_candidate_positive",
        "ready_for_official_release": False,
        "recommended_claim_level": level,
        "blocking_issues": issues,
        "required_next_run": "Controlled opt-in support review before any production support claim.",
        "workers_requested": execution.get("workers_requested", 1),
        "workers_used": execution.get("workers_used", 1),
        "downgrade_reason": execution.get("downgrade_reason", ""),
        "still_not_proven": list(STILL_NOT_PROVEN),
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "staged_opt_in_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
