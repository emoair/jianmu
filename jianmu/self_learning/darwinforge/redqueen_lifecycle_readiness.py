from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.process_lifecycle_schema import STILL_NOT_PROVEN_LIFECYCLE


def build_redqueen_lifecycle_readiness(
    output_records: str | Path,
    lifecycle_audit: Dict[str, Any],
    subprocess_guard: Dict[str, Any],
    executor_guard: Dict[str, Any],
    trace_guard: Dict[str, Any],
    git_audit: Dict[str, Any],
    sentinel: Dict[str, Any],
    short_replay: Dict[str, Any],
) -> Dict[str, Any]:
    blocking = []
    if sentinel.get("lingering_python_child_count", 0) > 0:
        blocking.append("lingering_python_process")
        level = "lifecycle_blocked_by_lingering_python"
    elif sentinel.get("lingering_git_process_count", 0) > 0:
        blocking.append("lingering_git_process")
        level = "lifecycle_blocked_by_lingering_git"
    elif sentinel.get("lingering_compiler_process_count", 0) > 0:
        blocking.append("lingering_compiler_process")
        level = "lifecycle_blocked_by_lingering_compiler"
    elif not executor_guard.get("executor_shutdown_guard_passed"):
        blocking.append("executor_shutdown_failed")
        level = "lifecycle_blocked_by_executor_shutdown"
    elif not trace_guard.get("trace_writer_shutdown_guard_passed"):
        blocking.append("trace_writer_shutdown_failed")
        level = "lifecycle_blocked_by_trace_writer"
    elif not all([
        subprocess_guard.get("subprocess_lifecycle_guard_passed"),
        git_audit.get("git_lifecycle_audit_passed"),
        sentinel.get("post_run_idle_sentinel_passed"),
        short_replay.get("redqueen_short_replay_passed"),
    ]):
        blocking.append("lifecycle_guard_failed")
        level = "failed"
    else:
        level = "redqueen_process_lifecycle_clean"
    result = {
        "lifecycle_repair_started": True,
        "lifecycle_repair_completed": level == "redqueen_process_lifecycle_clean",
        "process_lifecycle_audit_completed": lifecycle_audit.get("process_lifecycle_audit_completed", False),
        "subprocess_lifecycle_guard_passed": subprocess_guard.get("subprocess_lifecycle_guard_passed", False),
        "executor_shutdown_guard_passed": executor_guard.get("executor_shutdown_guard_passed", False),
        "trace_writer_shutdown_guard_passed": trace_guard.get("trace_writer_shutdown_guard_passed", False),
        "git_lifecycle_audit_passed": git_audit.get("git_lifecycle_audit_passed", False),
        "post_run_idle_sentinel_passed": sentinel.get("post_run_idle_sentinel_passed", False),
        "redqueen_short_replay_passed": short_replay.get("redqueen_short_replay_passed", False),
        "lingering_python_child_count": sentinel.get("lingering_python_child_count", 0),
        "lingering_git_process_count": sentinel.get("lingering_git_process_count", 0),
        "lingering_compiler_process_count": sentinel.get("lingering_compiler_process_count", 0),
        "lingering_generated_exe_count": sentinel.get("lingering_generated_exe_count", 0),
        "active_worker_thread_count": sentinel.get("active_worker_thread_count", 0),
        "open_manifest_handle_count": sentinel.get("open_manifest_handle_count", 0),
        "git_index_lock_leftover_detected": sentinel.get("git_index_lock_leftover_detected", False),
        "no_lingering_python_process": sentinel.get("lingering_python_child_count", 0) == 0,
        "no_lingering_git_process": sentinel.get("lingering_git_process_count", 0) == 0,
        "no_lingering_compiler_process": sentinel.get("lingering_compiler_process_count", 0) == 0,
        "no_non_daemon_worker_thread": sentinel.get("active_worker_thread_count", 0) == 0,
        "no_open_manifest_handle": sentinel.get("open_manifest_handle_count", 0) == 0,
        "no_git_index_lock": not sentinel.get("git_index_lock_leftover_detected", False),
        "workers_requested": short_replay.get("workers_requested", 16),
        "workers_used": short_replay.get("workers_used", 16),
        "compiler_workers_requested": short_replay.get("compiler_workers_requested", 16),
        "compiler_workers_used": short_replay.get("compiler_workers_used", 16),
        "downgrade_reason": short_replay.get("downgrade_reason", ""),
        "no_model_training": True,
        "no_weight_update": True,
        "reused_existing_logic": True,
        "default_profile_unchanged": short_replay.get("default_profile_unchanged", True),
        "explicit_opt_in_required": True,
        "staged_opt_in_enabled": True,
        "real_promotion_enabled": short_replay.get("real_promotion_enabled", False),
        "user_facing_enabled": False,
        "official_release_enabled": False,
        "production_function_support_completed": False,
        "production_array_support_completed": False,
        "production_recursion_support_completed": False,
        "redqueen_process_lifecycle_clean": level == "redqueen_process_lifecycle_clean",
        "ready_for_redqueen_iteration_2": level == "redqueen_process_lifecycle_clean",
        "redqueen_autonomous_governance_completed": False,
        "ready_for_official_release": False,
        "recommended_claim_level": level,
        "blocking_issues": blocking,
        "required_next_run": "RedQueen iteration 2; do not claim production support completed",
        "still_not_proven": list(STILL_NOT_PROVEN_LIFECYCLE),
    }
    _write_json(Path(output_records) / "redqueen_lifecycle_readiness.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
