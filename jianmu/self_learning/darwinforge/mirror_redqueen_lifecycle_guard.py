from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.post_run_idle_sentinel import run_post_run_idle_sentinel


def run_mirror_redqueen_lifecycle_guard(repo_root: str | Path, output_records: str | Path, idle_grace_seconds: int = 30) -> Dict[str, Any]:
    sentinel = run_post_run_idle_sentinel(repo_root, output_records, idle_grace_seconds=idle_grace_seconds)
    result = {
        "lifecycle_guard_completed": True,
        "final_post_run_idle_sentinel_passed": sentinel["post_run_idle_sentinel_passed"],
        "lingering_python_child_count": sentinel["lingering_python_child_count"],
        "lingering_git_process_count": sentinel["lingering_git_process_count"],
        "lingering_compiler_process_count": sentinel["lingering_compiler_process_count"],
        "lingering_generated_exe_count": sentinel["lingering_generated_exe_count"],
        "active_worker_thread_count": sentinel["active_worker_thread_count"],
        "open_manifest_handle_count": sentinel["open_manifest_handle_count"],
        "git_index_lock_leftover_detected": sentinel["git_index_lock_leftover_detected"],
    }
    result["lifecycle_guard_passed"] = all([
        result["final_post_run_idle_sentinel_passed"],
        result["lingering_python_child_count"] == 0,
        result["lingering_git_process_count"] == 0,
        result["lingering_compiler_process_count"] == 0,
        result["lingering_generated_exe_count"] == 0,
        result["active_worker_thread_count"] == 0,
        result["open_manifest_handle_count"] == 0,
        not result["git_index_lock_leftover_detected"],
    ])
    _write_json(Path(output_records) / "lifecycle_guard.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

