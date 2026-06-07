from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.production_path_reconciliation_schema import STILL_NOT_PROVEN


def build_production_bridge_scale_readiness(output_records: str | Path, reaudit: Dict[str, Any], scale: Dict[str, Any]) -> Dict[str, Any]:
    blocking: List[str] = []
    if not reaudit.get("phase_a_passed"):
        blocking.append("phase_a_failed")
    clean = (
        scale.get("cached_result_used_as_new_count", 1) == 0
        and scale.get("duplicate_invocation_id_count", 1) == 0
        and not scale.get("stubbed_validation_detected", True)
        and not scale.get("summary_only_validation_detected", True)
        and not scale.get("syntax_filter_used_as_correctness_evidence", True)
        and scale.get("wrong_stdout_count", 1) == 0
        and scale.get("timeout_count", 1) == 0
        and scale.get("permission_error_count", 1) == 0
        and scale.get("cleanup_failure_count", 1) == 0
    )
    if not clean:
        blocking.append("compiler_accounting_not_clean")
    if not scale.get("phase_b_started"):
        level = "reaudit_passed_scale_blocked" if reaudit.get("phase_a_passed") else "reaudit_failed"
    elif scale.get("wall_clock_hours", 0.0) >= 4 and scale.get("real_compiler_invocations", 0) >= 25000 and clean and scale.get("all_policy_categories_represented"):
        level = "extended_bridge_scale_positive"
    elif reaudit.get("phase_a_passed") and clean:
        level = "extended_bridge_positive_but_scale_partial"
    elif not reaudit.get("phase_a_passed"):
        level = "reaudit_failed"
    else:
        level = "failed"
    result = {
        "phase_a_passed": reaudit.get("phase_a_passed", False),
        "phase_b_started": scale.get("phase_b_started", False),
        "phase_b_completed": scale.get("phase_b_completed", False),
        "wall_clock_hours": scale.get("wall_clock_hours", 0.0),
        "wall_clock_minimum_satisfied": scale.get("wall_clock_minimum_satisfied", False),
        "hard_stop_hit": scale.get("hard_stop_hit", False),
        "function_ir_path_confirmed": reaudit.get("function_ir_path_confirmed", False),
        "array_ir_path_confirmed": reaudit.get("array_ir_path_confirmed", False),
        "function_array_ir_path_confirmed": reaudit.get("function_array_ir_path_confirmed", False),
        "recursion_ir_path_confirmed": reaudit.get("recursion_ir_path_confirmed", False),
        "atomic_policy_bridge_confirmed": reaudit.get("atomic_policy_bridge_confirmed", False),
        "template_bypass_detected": reaudit.get("template_bypass_detected", False),
        "marker_ir_direct_compile_detected": reaudit.get("marker_ir_direct_compile_detected", False),
        "rewrite_violation_detected": reaudit.get("rewrite_violation_detected", False),
        "reuse_existing_logic_confirmed": reaudit.get("reuse_existing_logic_confirmed", False),
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "experimental_function_array_recursion_bridge_scaled": level in {"extended_bridge_scale_positive", "extended_bridge_positive_but_scale_partial"},
        "ready_for_real_capability_review": reaudit.get("phase_a_passed", False) and clean,
        "ready_for_official_release": False,
        "recommended_claim_level": level,
        "blocking_issues": blocking + list(reaudit.get("phase_a_blocking_issues", [])),
        "required_next_run": "Repeat scale validation until wall_clock_hours >= 4 and real_compiler_invocations >= 25000, then review before any production-profile work.",
        "still_not_proven": list(STILL_NOT_PROVEN),
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "production_bridge_scale_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result

