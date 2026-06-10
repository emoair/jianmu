from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.controlled_profile_review_schema import STILL_NOT_PROVEN


def build_controlled_profile_review_readiness(
    output_records: str | Path,
    source: Dict[str, Any],
    shadow: Dict[str, Any],
    contamination: Dict[str, Any],
    adapter: Dict[str, Any],
    coverage: Dict[str, Any],
    windows: Dict[str, Any],
    replay: Dict[str, Any],
    rollback: Dict[str, Any],
    precheck: Dict[str, Any],
) -> Dict[str, Any]:
    blocking: List[str] = []
    if not source.get("source_dry_run_records_found"):
        blocking.append("missing_v1_0_6_records")
        level = "controlled_review_blocked_missing_v1_0_6_records"
    elif contamination.get("default_profile_contamination_detected"):
        blocking.append("default_profile_contamination")
        level = "controlled_review_failed_default_contamination"
    elif not windows.get("windows_write_isolation_passed"):
        blocking.append("windows_write_isolation")
        level = "controlled_review_blocked_windows_write_isolation"
    elif not replay.get("trace_pack_replayability_passed"):
        blocking.append("trace_replay_failed")
        level = "controlled_review_replay_failed"
    elif not rollback.get("rollback_stress_passed"):
        blocking.append("rollback_stress_failed")
        level = "failed"
    else:
        coverage_notes = bool(coverage.get("coverage_review_notes"))
        level = "controlled_review_positive_with_coverage_notes" if coverage_notes else "controlled_profile_review_positive"
    result = {
        "source_dry_run_records_found": source.get("source_dry_run_records_found", False),
        "controlled_profile_review_completed": True,
        "shadow_profile_valid": shadow.get("shadow_profile_valid", False),
        "explicit_opt_in_confirmed": shadow.get("explicit_opt_in_confirmed", False),
        "default_profile_contamination_detected": contamination.get("default_profile_contamination_detected", True),
        "default_profile_unchanged": not contamination.get("default_profile_contamination_detected", True),
        "real_promotion_enabled": False,
        "user_facing_enabled": False,
        "staged_opt_in_enabled": False,
        "interface_adapter_review_completed": adapter.get("interface_adapter_review_completed", False),
        "adapter_interface_valid": adapter.get("adapter_interface_valid", False),
        "direct_template_path_detected": adapter.get("direct_template_path_detected", True),
        "marker_ir_direct_compile_detected": adapter.get("marker_ir_direct_compile_detected", True),
        "summary_only_validation_detected": adapter.get("summary_only_validation_detected", True),
        "coverage_review_completed": coverage.get("coverage_review_completed", False),
        "unique_compile_unit_count": coverage.get("unique_compile_unit_count", 0),
        "source_sha256_unique_count": coverage.get("source_sha256_unique_count", 0),
        "policy_distribution": coverage.get("policy_distribution", {}),
        "category_all_represented": coverage.get("category_all_represented", False),
        "coverage_skew_detected": coverage.get("coverage_skew_detected", True),
        "windows_records_write_audit_completed": windows.get("windows_records_write_audit_completed", False),
        "windows_write_isolation_passed": windows.get("windows_write_isolation_passed", False),
        "isolation_fix_applied": windows.get("isolation_fix_applied", False),
        "trace_replay_completed": replay.get("trace_replay_completed", False),
        "replay_sample_count": replay.get("replay_sample_count", 0),
        "replay_success_rate": replay.get("replay_success_rate", 0.0),
        "replay_fail_count": replay.get("replay_fail_count", 0),
        "replay_stdout_mismatch_count": replay.get("replay_stdout_mismatch_count", 0),
        "replay_policy_path_drift_count": replay.get("replay_policy_path_drift_count", 0),
        "rollback_stress_completed": rollback.get("rollback_stress_completed", False),
        "rollback_cycles": rollback.get("rollback_cycles", 0),
        "rollback_cycle_fail_count": rollback.get("rollback_cycle_fail_count", 0),
        "rollback_stress_passed": rollback.get("rollback_stress_passed", False),
        "staged_opt_in_executed": precheck.get("staged_opt_in_executed", False),
        "ready_for_staged_opt_in_candidate": precheck.get("ready_for_staged_opt_in_candidate", False) and level.startswith("controlled_"),
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "ready_for_official_release": False,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "v1.0.7 staged opt-in profile candidate only after human approval; do not enable production support.",
        "workers_requested": replay.get("workers_requested", 1),
        "workers_used": replay.get("workers_used", 1),
        "downgrade_reason": replay.get("downgrade_reason", ""),
        "still_not_proven": list(STILL_NOT_PROVEN),
    }
    _write_json(Path(output_records) / "controlled_profile_review_readiness.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
