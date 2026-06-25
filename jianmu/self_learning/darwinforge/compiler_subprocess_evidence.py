from __future__ import annotations

import hashlib
import subprocess
import time
from pathlib import Path
from typing import Dict, List

from jianmu.self_learning.darwinforge.security_interference_detector import classify_security_interference


def run_process_evidence(command: List[str], cwd: Path, stdout_path: Path, stderr_path: Path, timeout: int = 30) -> Dict[str, object]:
    start = time.monotonic()
    timed_out = False
    try:
        proc = subprocess.Popen(command, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        pid = proc.pid
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            stdout, stderr = proc.communicate(timeout=5)
        returncode = proc.returncode
    except Exception as exc:  # noqa: BLE001
        pid = -1
        stdout = ""
        stderr = repr(exc)
        returncode = -999
    end = time.monotonic()
    stdout_path.write_text(stdout, encoding="utf-8", errors="replace")
    stderr_path.write_text(stderr, encoding="utf-8", errors="replace")
    security = classify_security_interference(stderr)
    return {
        "command": command,
        "pid": pid,
        "start_monotonic": start,
        "end_monotonic": end,
        "returncode": returncode,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "timed_out": timed_out,
        **security,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
