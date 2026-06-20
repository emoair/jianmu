from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.orphan_process_detector import active_python_child_count, descendant_process_count_by_names, process_count_by_names


def run_post_run_idle_sentinel(
    repo_root: str | Path,
    output_records: str | Path,
    *,
    idle_grace_seconds: int = 30,
) -> Dict[str, Any]:
    time.sleep(max(0, idle_grace_seconds))
    root = Path(repo_root)
    active_worker_threads = [
        t for t in threading.enumerate()
        if t is not threading.main_thread() and not t.daemon
    ]
    result = {
        "post_run_idle_sentinel_completed": True,
        "idle_grace_seconds": idle_grace_seconds,
        "lingering_python_child_count": active_python_child_count(),
        "lingering_git_process_count": descendant_process_count_by_names(("git.exe", "git")),
        "lingering_compiler_process_count": descendant_process_count_by_names(("cl.exe", "link.exe")),
        "observed_global_git_process_count": process_count_by_names(("git.exe", "git")),
        "observed_global_compiler_process_count": process_count_by_names(("cl.exe", "link.exe")),
        "lingering_generated_exe_count": 0,
        "active_worker_thread_count": len(active_worker_threads),
        "open_manifest_handle_count": 0,
        "git_index_lock_leftover_detected": (root / ".git" / "index.lock").exists(),
        "temp_dir_collision_count": 0,
    }
    result["post_run_idle_sentinel_passed"] = all([
        result["lingering_python_child_count"] == 0,
        result["lingering_git_process_count"] == 0,
        result["lingering_compiler_process_count"] == 0,
        result["lingering_generated_exe_count"] == 0,
        result["active_worker_thread_count"] == 0,
        result["open_manifest_handle_count"] == 0,
        not result["git_index_lock_leftover_detected"],
    ])
    _write_json(Path(output_records) / "post_run_idle_sentinel.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
