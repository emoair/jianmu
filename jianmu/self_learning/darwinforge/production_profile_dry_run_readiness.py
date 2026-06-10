from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.production_profile_dry_run_schema import STILL_NOT_PROVEN


def build_production_profile_dry_run_readiness(
    output_records: str | Path,
    shadow: Dict[str, Any],
    guard: Dict[str, Any],
    adapter: Dict[str, Any],
    execution: Dict[str, Any],
    regression: Dict[str, Any],
    rollback: Dict[str, Any],
) -> Dict[str, Any]:
    blocking: List[str] = []
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
    if not guard.get("dry_run_profile_guard_passed"):
        blocking.append("guard_failed")
        level = "dry_run_guard_failed"
    elif not regression.get("regression_guard_passed"):
        blocking.append("regression_guard_failed")
        level = "dry_run_regression_failed"
    elif not rollback.get("rollback_test_passed"):
        blocking.append("rollback_failed")
        level = "dry_run_rollback_failed"
    elif not clean_accounting:
        blocking.append("compiler_accounting_not_clean")
        level = "failed"
    elif execution.get("wall_clock_hours", 0.0) >= 4 and execution.get("real_compiler_invocations", 0) >= 40_000 and execution.get("all_policy_categories_represented") and execution.get("trace_pack_replayable"):
        level = "production_profile_dry_run_positive"
    elif execution.get("production_dry_run_executed") and clean_accounting:
        level = "dry_run_positive_but_scale_partial"
    else:
        blocking.append("dry_run_not_executed_or_incomplete")
        level = "failed"
    result = {
        "shadow_profile_created": shadow.get("shadow_profile_created", False),
        "shadow_profile_name": shadow.get("profile_name", ""),
        "default_profile_unchanged": shadow.get("default_profile_unchanged", False),
        "real_promotion_enabled": shadow.get("real_promotion_enabled", True),
        "production_dry_run_executed": execution.get("production_dry_run_executed", False),
        "user_facing_enabled": shadow.get("user_facing_enabled", True),
        "dry_run_profile_guard_passed": guard.get("dry_run_profile_guard_passed", False),
        "adapter_interface_valid": adapter.get("adapter_interface_valid", False),
        "adapter_reuses_atomic_policy_bridge": adapter.get("adapter_reuses_atomic_policy_bridge", False),
        "adapter_reuses_extended_ir": adapter.get("adapter_reuses_extended_ir", False),
        "adapter_reuses_extended_emitter": adapter.get("adapter_reuses_extended_emitter", False),
        "adapter_reuses_compiler_backend": adapter.get("adapter_reuses_compiler_backend", False),
        "direct_template_path_detected": adapter.get("direct_template_path_detected", False),
        "marker_ir_direct_compile_detected": adapter.get("marker_ir_direct_compile_detected", False),
        "summary_only_validation_detected": adapter.get("summary_only_validation_detected", False) or execution.get("summary_only_validation_detected", False),
        "arithmetic_regression_compile_success_rate": execution.get("arithmetic_regression_compile_success_rate", 0.0),
        "function_dry_run_success_rate": execution.get("function_dry_run_success_rate", 0.0),
        "array_dry_run_success_rate": execution.get("array_dry_run_success_rate", 0.0),
        "function_array_dry_run_success_rate": execution.get("function_array_dry_run_success_rate", 0.0),
        "structured_recursion_dry_run_success_rate": execution.get("structured_recursion_dry_run_success_rate", 0.0),
        "mixed_dry_run_success_rate": execution.get("mixed_dry_run_success_rate", 0.0),
        "wall_clock_hours": execution.get("wall_clock_hours", 0.0),
        "wall_clock_minimum_satisfied": execution.get("wall_clock_minimum_satisfied", False),
        "hard_stop_hit": execution.get("hard_stop_hit", False),
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
        "rollback_test_passed": rollback.get("rollback_test_passed", False),
        "trace_pack_generated": execution.get("trace_pack_generated", False),
        "trace_pack_replayable": execution.get("trace_pack_replayable", False),
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "ready_for_controlled_profile_review": level == "production_profile_dry_run_positive",
        "ready_for_official_release": False,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "Controlled profile review by humans before any production-profile integration work.",
        "workers_requested": execution.get("workers_requested", 1),
        "workers_used": execution.get("workers_used", 1),
        "downgrade_reason": execution.get("downgrade_reason", ""),
        "still_not_proven": list(STILL_NOT_PROVEN),
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "production_profile_dry_run_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
