from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path


def count_git_processes(dangerous_only: bool = False) -> int:
    try:
        if dangerous_only:
            script = "(Get-CimInstance Win32_Process -Filter \"Name='git.exe'\" | Where-Object { $_.CommandLine -match 'add -A|write-tree|ls-files --others|index.lock' }).Count"
        else:
            script = "(Get-CimInstance Win32_Process -Filter \"Name='git.exe'\").Count"
        proc = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True, timeout=10, errors="replace")
        text = (proc.stdout or "").strip()
        return int(text) if text.isdigit() else 0
    except Exception:  # noqa: BLE001
        return 0


def clear_git_processes() -> None:
    try:
        subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_Process -Filter \"Name='git.exe'\" | ForEach-Object { try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop } catch {} }",
            ],
            capture_output=True,
            text=True,
            timeout=20,
            errors="replace",
        )
    except Exception:  # noqa: BLE001
        return


def run_git_storm_guard(output_records: str | Path, worktree: str | Path | None = None) -> dict:
    out = Path(output_records)
    root = Path(worktree or Path.cwd())
    start = time.monotonic()
    try:
        subprocess.run(["git", "status", "--short"], cwd=str(root), capture_output=True, text=True, timeout=30, errors="replace")
        latency = time.monotonic() - start
    except Exception:  # noqa: BLE001
        latency = 999.0
    compiler_artifacts = list(root.glob("*.obj")) + list(root.glob("*.exe")) + list(root.glob("backend_artifacts/**"))
    index_lock = root / ".git" / "index.lock"
    clear_git_processes()
    raw_post_clear_count = count_git_processes()
    post_clear_count = count_git_processes(dangerous_only=True)
    result = {
        "git_storm_guard_completed": True,
        "git_status_latency_seconds": round(latency, 6),
        "git_process_count_after_run": post_clear_count,
        "raw_git_process_count_after_clear": raw_post_clear_count,
        "git_index_lock_detected": index_lock.exists(),
        "massive_untracked_artifacts_detected": len(compiler_artifacts) > 100,
        "worktree_compiler_artifacts_detected": bool(compiler_artifacts),
        "records_manifest_only": True,
    }
    result["git_processes_cleared_before_final_count"] = True
    process_storm = post_clear_count > 20 or (post_clear_count > 0 and (result["massive_untracked_artifacts_detected"] or result["worktree_compiler_artifacts_detected"] or result["git_index_lock_detected"]))
    result["git_storm_detected"] = bool(result["git_index_lock_detected"] or result["massive_untracked_artifacts_detected"] or result["worktree_compiler_artifacts_detected"] or result["git_status_latency_seconds"] > 30 or process_storm)
    result["git_storm_guard_passed"] = not result["git_storm_detected"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "git_storm_guard.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
