from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.post_run_idle_sentinel import run_post_run_idle_sentinel


def run_stability_lifecycle_guard(repo_root: str | Path, output_records: str | Path, cycle_result: Dict[str, Any], idle_grace_seconds: int = 30) -> Dict[str, Any]:
    sentinel = run_post_run_idle_sentinel(repo_root, output_records, idle_grace_seconds=idle_grace_seconds)
    checkpoints = [cycle["lifecycle"] for cycle in cycle_result.get("cycles", [])]
    result = {
        "multiround_lifecycle_guard_completed": True,
        "cycle_lifecycle_checkpoints": checkpoints,
        "final_post_run_idle_sentinel_passed": sentinel.get("post_run_idle_sentinel_passed", False),
        "lingering_python_child_count": sentinel.get("lingering_python_child_count", 0),
        "lingering_git_process_count": sentinel.get("lingering_git_process_count", 0),
        "lingering_compiler_process_count": sentinel.get("lingering_compiler_process_count", 0),
        "lingering_generated_exe_count": sentinel.get("lingering_generated_exe_count", 0),
        "active_worker_thread_count": sentinel.get("active_worker_thread_count", 0),
        "open_manifest_handle_count": sentinel.get("open_manifest_handle_count", 0),
        "git_index_lock_leftover_detected": sentinel.get("git_index_lock_leftover_detected", False),
    }
    result["lifecycle_clean_after_multiround"] = all([
        result["final_post_run_idle_sentinel_passed"],
        result["lingering_python_child_count"] == 0,
        result["lingering_git_process_count"] == 0,
        result["lingering_compiler_process_count"] == 0,
        result["lingering_generated_exe_count"] == 0,
        result["active_worker_thread_count"] == 0,
        result["open_manifest_handle_count"] == 0,
        not result["git_index_lock_leftover_detected"],
    ])
    result["multiround_lifecycle_guard_passed"] = result["lifecycle_clean_after_multiround"] and all(
        checkpoint.get("cycle_lifecycle_checkpoint_passed", False) for checkpoint in checkpoints
    )
    _write_json(Path(output_records) / "multiround_lifecycle_guard.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
