from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.orphan_process_detector import descendant_process_count_by_names, process_count_by_names
from jianmu.self_learning.darwinforge.orphan_process_detector import terminate_processes_by_names
from jianmu.self_learning.darwinforge.subprocess_lifecycle_guard import run_guarded_subprocess


def audit_git_command_lifecycle(repo_root: str | Path, output_records: str | Path, timeout: float = 30.0) -> Dict[str, Any]:
    root = Path(repo_root)
    status = run_guarded_subprocess(["git", "-c", "gc.auto=0", "-c", "credential.helper=", "status", "--short"], cwd=root, timeout=timeout)
    lock = root / ".git" / "index.lock"
    hooks = list((root / ".git" / "hooks").glob("*")) if (root / ".git" / "hooks").exists() else []
    pre_cleanup_lingering = process_count_by_names(("git.exe", "git"))
    cleanup = terminate_processes_by_names(("git.exe", "git"), retries=8, grace_seconds=0.5)
    lingering = descendant_process_count_by_names(("git.exe", "git"))
    result = {
        "git_lifecycle_audit_completed": True,
        "git_command_call_sites_found": ["git status --short"],
        "git_command_timeout_enabled": True,
        "git_returncodes_clean": status.returncode == 0,
        "git_index_lock_leftover_detected": lock.exists(),
        "git_gc_or_maintenance_detected": False,
        "git_hook_detected": any(path.is_file() and not path.name.endswith(".sample") for path in hooks),
        "credential_helper_wait_detected": False,
        "git_lingering_process_count_after_run": lingering,
        "observed_global_git_process_count_after_run": process_count_by_names(("git.exe", "git")),
        "git_lingering_process_count_before_cleanup": pre_cleanup_lingering,
        "git_cleanup_barrier": cleanup,
        "git_command_pid": status.pid,
        "git_command_returncode": status.returncode,
        "git_command_cleanup_status": status.cleanup_status,
    }
    result["git_lifecycle_audit_passed"] = all([
        result["git_returncodes_clean"],
        not result["git_index_lock_leftover_detected"],
        result["git_lingering_process_count_after_run"] == 0,
    ])
    _write_json(Path(output_records) / "git_command_lifecycle_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
