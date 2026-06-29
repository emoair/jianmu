from __future__ import annotations

import json
from pathlib import Path


def build_dataset_backend6h_readiness(output_records: str | Path, payload: dict) -> dict:
    blocking: list[str] = []
    checks = {
        "threshold_calibration_passed": "threshold_calibration_failed",
        "dataset_training_passed": "dataset_training_failed",
        "split_guard_passed": "split_guard_failed",
        "redqueen_dataset_scheduler_passed": "redqueen_scheduler_failed",
        "mirror_feedback_passed": "mirror_feedback_failed",
        "backend6h_validation_passed": "backend6h_validation_failed",
        "dataset_evidence_pack_passed": "dataset_evidence_pack_failed",
        "repo_hygiene_guard_passed": "repo_hygiene_failed",
        "trace_shard_size_cap_passed": "trace_shard_size_cap_failed",
        "memory_guard_passed": "memory_guard_failed",
        "lifecycle_guard_passed": "lifecycle_guard_failed",
    }
    for key, issue in checks.items():
        if not payload.get(key):
            blocking.append(issue)
    if payload.get("leakage_detected") or payload.get("train_heldout_leakage_detected"):
        blocking.append("train_heldout_leakage_detected")
    if payload.get("real_promotion_enabled"):
        blocking.append("real_promotion_enabled")
    if "train_heldout_leakage_detected" in blocking or "split_guard_failed" in blocking:
        recommended = "dataset_training_blocked_by_split_leakage"
    elif "backend6h_validation_failed" in blocking:
        recommended = "backend6h_blocked_by_threshold"
    elif any(item in blocking for item in ("repo_hygiene_failed", "memory_guard_failed", "lifecycle_guard_failed")):
        recommended = "blocked_by_git_or_memory_hygiene"
    elif blocking:
        recommended = "failed"
    else:
        recommended = "active_work_calibrated_dataset_training_backend6h_positive"
    result = {
        **payload,
        "train_heldout_split_guard_passed": bool(payload.get("split_guard_passed")),
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
        "real_promotion_enabled": False,
        "default_profile_unchanged": True,
        "recommended_claim_level": recommended,
        "blocking_issues": blocking,
        "required_next_run": "Pure validation on the newly trained incremental dataset before any production-boundary discussion.",
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "dataset_backend6h_readiness.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
