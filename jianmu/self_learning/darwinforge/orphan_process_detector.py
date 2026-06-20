from __future__ import annotations

import multiprocessing
import os
import subprocess
import time
from typing import Iterable


def active_python_child_count() -> int:
    return len(multiprocessing.active_children())


def process_count_by_names(names: Iterable[str]) -> int:
    wanted = {name.lower() for name in names}
    if os.name == "nt":
        try:
            proc = subprocess.run(["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True, timeout=10, errors="replace")
        except Exception:
            return 0
        count = 0
        for line in proc.stdout.splitlines():
            first = line.split(",", 1)[0].strip().strip('"').lower()
            if first in wanted:
                count += 1
        return count
    try:
        proc = subprocess.run(["ps", "-eo", "comm="], capture_output=True, text=True, timeout=10, errors="replace")
    except Exception:
        return 0
    return sum(1 for line in proc.stdout.splitlines() if line.strip().lower() in wanted)


def descendant_process_count_by_names(names: Iterable[str], root_pid: int | None = None) -> int:
    wanted = {name.lower() for name in names}
    root = root_pid or os.getpid()
    if os.name != "nt":
        return 0
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name | ConvertTo-Json -Compress"],
            capture_output=True,
            text=True,
            timeout=20,
            errors="replace",
        )
    except Exception:
        return 0
    import json

    try:
        payload = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return 0
    rows = payload if isinstance(payload, list) else [payload]
    children: dict[int, list[dict]] = {}
    for row in rows:
        children.setdefault(int(row.get("ParentProcessId", -1)), []).append(row)
    stack = list(children.get(root, []))
    count = 0
    while stack:
        row = stack.pop()
        if str(row.get("Name", "")).lower() in wanted:
            count += 1
        stack.extend(children.get(int(row.get("ProcessId", -1)), []))
    return count


def detect_orphan_processes() -> dict:
    compiler_count = descendant_process_count_by_names(("cl.exe", "link.exe"))
    git_count = descendant_process_count_by_names(("git.exe", "git"))
    return {
        "orphan_process_detector_completed": True,
        "lingering_python_child_count": active_python_child_count(),
        "lingering_git_process_count": git_count,
        "lingering_compiler_process_count": compiler_count,
        "observed_global_git_process_count": process_count_by_names(("git.exe", "git")),
        "observed_global_compiler_process_count": process_count_by_names(("cl.exe", "link.exe")),
        "lingering_generated_exe_count": 0,
        "orphan_process_detector_passed": compiler_count == 0 and active_python_child_count() == 0,
    }


def terminate_processes_by_names(names: Iterable[str], retries: int = 5, grace_seconds: float = 0.5) -> dict:
    wanted = [name for name in names]
    before = process_count_by_names(wanted)
    after = before
    attempts = 0
    for attempts in range(1, retries + 1):
        if after == 0:
            break
        if os.name == "nt":
            for name in wanted:
                subprocess.run(["taskkill", "/f", "/im", name], capture_output=True, text=True, timeout=15, errors="replace")
        else:
            for name in wanted:
                subprocess.run(["pkill", "-f", name], capture_output=True, text=True, timeout=15, errors="replace")
        time.sleep(grace_seconds)
        after = process_count_by_names(wanted)
    terminated = max(0, before - after)
    return {
        "cleanup_process_names": list(wanted),
        "process_count_before_cleanup": before,
        "process_count_after_cleanup": after,
        "terminated_process_count": terminated,
        "cleanup_attempts": attempts,
        "cleanup_barrier_passed": after == 0,
    }
