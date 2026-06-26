from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path


GIT_NAMES = ("git.exe", "git-lfs.exe", "git-remote-https.exe", "git-credential-manager.exe", "scalar.exe")


def snapshot_git_processes() -> list[dict]:
    script = (
        "Get-CimInstance Win32_Process | Where-Object { "
        "$_.Name -in @('git.exe','git-lfs.exe','git-remote-https.exe','git-credential-manager.exe','scalar.exe','sh.exe','bash.exe') "
        "} | Select-Object ProcessId,Name,ExecutablePath,CommandLine | ConvertTo-Json -Compress"
    )
    try:
        proc = subprocess.run(["powershell", "-NoProfile", "-Command", script], capture_output=True, text=True, timeout=15, errors="replace")
        text = (proc.stdout or "").strip()
        if not text:
            return []
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except Exception:  # noqa: BLE001
        return []


def classify_git_root_cause(processes: list[dict], worktree_artifact_count: int, records_large_file_count: int) -> str:
    commands = " ".join(str(p.get("CommandLine", "")) for p in processes).lower()
    if worktree_artifact_count > 100:
        return "worktree_artifact_storm"
    if records_large_file_count > 0:
        return "records_large_shard_storm"
    if "ls-files --others" in commands or "write-tree" in commands or "status --porcelain" in commands:
        return "ide_git_integration"
    if "maintenance" in commands or " gc" in commands:
        return "git_maintenance"
    if "credential" in commands:
        return "credential_helper"
    return "unknown" if processes else "none"


def audit_git_residual_processes(output_records: str | Path, *, worktree: str | Path = ".") -> dict:
    out = Path(output_records)
    root = Path(worktree)
    before = snapshot_git_processes()
    start = time.monotonic()
    try:
        subprocess.run(["git", "status", "--short"], cwd=str(root), capture_output=True, text=True, timeout=60, errors="replace")
        latency = time.monotonic() - start
    except Exception:  # noqa: BLE001
        latency = 999.0
    worktree_artifacts = list(root.glob("*.obj")) + list(root.glob("*.exe")) + list(root.glob("backend_artifacts/**"))
    large_records = [p for p in (root / "records").rglob("*") if p.is_file() and p.stat().st_size >= 50_000_000] if (root / "records").exists() else []
    after = snapshot_git_processes()
    time.sleep(1)
    after_idle = snapshot_git_processes()
    result = {
        "git_residual_audit_completed": True,
        "git_processes_before": len(before),
        "git_processes_after": len(after),
        "git_processes_after_idle": len(after_idle),
        "git_for_windows_residual_detected": len(after_idle) > 0,
        "git_index_lock_detected": (root / ".git" / "index.lock").exists(),
        "git_status_latency_seconds": round(latency, 6),
        "worktree_artifact_count": len(worktree_artifacts),
        "untracked_artifact_count": len(worktree_artifacts),
        "records_large_file_count": len(large_records),
        "suspected_git_storm_sources": [str(p) for p in large_records[:20]],
    }
    result["git_residual_root_cause"] = classify_git_root_cause(after_idle or after or before, len(worktree_artifacts), len(large_records))
    result["git_residual_audit_passed"] = not result["git_index_lock_detected"] and result["git_status_latency_seconds"] < 60
    out.mkdir(parents=True, exist_ok=True)
    (out / "git_residual_process_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
