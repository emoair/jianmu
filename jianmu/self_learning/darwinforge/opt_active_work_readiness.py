from __future__ import annotations

import json
from pathlib import Path


def build_opt_active_work_readiness(output_records: str | Path, payload: dict) -> dict:
    blocking: list[str] = []
    if not payload.get("active_work_audit_completed"):
        blocking.append("active_work_audit_missing")
    if not payload.get("opt_active_work_rate_contract_passed"):
        blocking.append("opt_active_work_rate_contract_failed")
    if not payload.get("idle_padding_detector_passed"):
        blocking.append("idle_padding_detector_failed")
    if not payload.get("opt_backend_consistency_audit_passed"):
        blocking.append("opt_backend_consistency_failed")
    if not payload.get("too_perfect_output_detector_passed"):
        blocking.append("too_perfect_output_detected")
    if not payload.get("git_residual_audit_passed"):
        blocking.append("git_residual_audit_failed")
    if not payload.get("git_cleanup_guard_passed"):
        blocking.append("git_cleanup_guard_failed")
    if not payload.get("trace_shard_size_cap_passed"):
        blocking.append("trace_shard_size_cap_failed")
    if not payload.get("active_backend_validation_passed"):
        blocking.append("active_backend_validation_failed")
    if payload.get("real_promotion_enabled"):
        blocking.append("real_promotion_enabled")
    recommended = "opt_active_work_git_lifecycle_repaired"
    if "idle_padding_detector_failed" in blocking:
        recommended = "active_work_blocked_by_idle_padding"
    elif "opt_backend_consistency_failed" in blocking:
        recommended = "active_work_blocked_by_manifest_mismatch"
    elif "git_cleanup_guard_failed" in blocking or "git_residual_audit_failed" in blocking:
        recommended = "blocked_by_git_residual_process"
    elif "trace_shard_size_cap_failed" in blocking:
        recommended = "blocked_by_trace_shard_cap"
    elif blocking:
        recommended = "failed"
    result = {
        **payload,
        "opt_active_work_git_lifecycle_repaired": not blocking,
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
        "recommended_claim_level": recommended,
        "blocking_issues": blocking,
        "required_next_run": "Human review of active-work-rate and Git lifecycle evidence before any longer validation.",
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "opt_active_work_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
