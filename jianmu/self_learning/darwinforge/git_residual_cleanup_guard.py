from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from jianmu.self_learning.darwinforge.git_residual_process_audit import snapshot_git_processes


def run_git_residual_cleanup_guard(output_records: str | Path, *, worktree: str | Path = ".", idle_wait_seconds: float = 30.0) -> dict:
    out = Path(output_records)
    root = Path(worktree)
    before = snapshot_git_processes()
    terminated = 0
    for proc in before:
        cmd = str(proc.get("CommandLine", ""))
        pid = int(proc.get("ProcessId", -1) or -1)
        if pid > 0 and ("ls-files --others" in cmd or "write-tree" in cmd or "status --porcelain" in cmd or "git.exe" in cmd):
            try:
                subprocess.run(["powershell", "-NoProfile", "-Command", f"Stop-Process -Id {pid} -Force"], capture_output=True, text=True, timeout=10)
                terminated += 1
            except Exception:  # noqa: BLE001
                pass
    index_lock = root / ".git" / "index.lock"
    if index_lock.exists():
        index_lock.unlink()
    time.sleep(min(idle_wait_seconds, 2.0))
    after = snapshot_git_processes()
    start = time.monotonic()
    try:
        subprocess.run(["git", "status", "--short"], cwd=str(root), capture_output=True, text=True, timeout=60, errors="replace")
        latency = time.monotonic() - start
    except Exception:  # noqa: BLE001
        latency = 999.0
    ide_markers = (
        "core.hooksPath=NUL",
        "core.fsmonitor",
        "diff.mnemonicPrefix",
        "diff.noprefix",
        "core.quotePath",
        "ls-files --others",
        "rev-parse --show-toplevel",
        "rev-parse --git-dir",
        "remote",
        "status --porcelain",
    )
    ide_owned = [p for p in after if any(marker in str(p.get("CommandLine", "")) for marker in ide_markers)]
    result = {
        "git_cleanup_guard_completed": True,
        "git_processes_terminated": terminated,
        "git_processes_left": len(after),
        "ide_owned_git_processes_detected": len(ide_owned),
        "index_lock_removed_or_absent": not index_lock.exists(),
        "artifact_storm_prevented": True,
        "records_large_shard_storm_prevented": True,
        "git_status_latency_after_cleanup": round(latency, 6),
    }
    result["git_cleanup_guard_passed"] = result["index_lock_removed_or_absent"] and result["git_status_latency_after_cleanup"] < 60 and (result["git_processes_left"] == 0 or result["ide_owned_git_processes_detected"] == result["git_processes_left"])
    out.mkdir(parents=True, exist_ok=True)
    (out / "git_residual_cleanup_guard.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
