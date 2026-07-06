from __future__ import annotations

import json
from pathlib import Path


def build_memory_repair_readiness(output_records: str | Path, payload: dict) -> dict:
    blocking: list[str] = []
    checks = {
        "memory_pressure_audit_completed": "memory_pressure_audit_missing",
        "memory_snapshot_contract_passed": "memory_snapshot_contract_failed",
        "streaming_dataset_writer_passed": "memory_repair_blocked_by_giant_list",
        "streaming_manifest_writer_passed": "streaming_manifest_failed",
        "bounded_queue_backpressure_passed": "memory_repair_blocked_by_queue_growth",
        "subprocess_output_streaming_passed": "memory_repair_blocked_by_subprocess_buffering",
        "cycle_cleanup_barrier_passed": "cycle_cleanup_barrier_failed",
        "memory_pressure_checkpoint_passed": "memory_pressure_checkpoint_failed",
        "memory_stress_validation_passed": "memory_repair_blocked_by_stress_validation",
        "trace_shard_size_cap_passed": "trace_shard_size_cap_failed",
        "git_cleanup_guard_passed": "git_cleanup_guard_failed",
        "lifecycle_guard_passed": "lifecycle_guard_failed",
    }
    for key, issue in checks.items():
        if not payload.get(key):
            blocking.append(issue)
    if payload.get("giant_list_detected"):
        blocking.append("memory_repair_blocked_by_giant_list")
    if payload.get("memory_hard_stop_triggered"):
        blocking.append("memory_repair_blocked_by_stress_validation")
    if payload.get("real_promotion_enabled"):
        blocking.append("real_promotion_enabled")
    if not blocking:
        recommended = "memory_lifecycle_streaming_repair_positive"
    elif payload.get("memory_stress_validation_passed") and payload.get("memory_warning_triggered"):
        recommended = "memory_repair_positive_with_pressure_notes"
    elif "memory_repair_blocked_by_giant_list" in blocking:
        recommended = "memory_repair_blocked_by_giant_list"
    elif "memory_repair_blocked_by_queue_growth" in blocking:
        recommended = "memory_repair_blocked_by_queue_growth"
    elif "memory_repair_blocked_by_subprocess_buffering" in blocking:
        recommended = "memory_repair_blocked_by_subprocess_buffering"
    elif "memory_repair_blocked_by_stress_validation" in blocking:
        recommended = "memory_repair_blocked_by_stress_validation"
    else:
        recommended = "failed"
    result = {
        **payload,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
        "real_promotion_enabled": False,
        "default_profile_unchanged": True,
        "recommended_claim_level": recommended,
        "blocking_issues": sorted(set(blocking)),
        "required_next_run": "Pure heldout validation on the incremental dataset after memory lifecycle repair.",
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "memory_repair_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
