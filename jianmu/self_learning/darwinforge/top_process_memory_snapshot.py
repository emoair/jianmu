from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from jianmu.self_learning.darwinforge.security_onedrive_git_classifier import classify_process


def collect_top_process_memory(limit: int = 20) -> dict:
    rows = _collect_process_rows()
    rows.sort(key=lambda row: row.get("rss_mb", 0.0), reverse=True)
    top = []
    for row in rows[:limit]:
        row["classification"] = classify_process(row.get("name", ""), row.get("cmdline", ""))
        top.append(row)
    return {"timestamp": datetime.now(timezone.utc).isoformat(), "monotonic": time.monotonic(), "top_processes": top}


def write_top_process_snapshot_contract(output_records: str | Path, timeline_path: str | Path, *, top_n: int = 20) -> dict:
    path = Path(timeline_path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.exists() else []
    result = {
        "top_process_snapshot_implemented": True,
        "top_process_snapshot_passed": bool(rows) and all(len(row.get("top_processes", [])) <= top_n for row in rows),
        "top_process_timeline_rows": len(rows),
        "record_top_processes": top_n,
    }
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "top_process_memory_snapshot.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _collect_process_rows() -> list[dict]:
    ps = (
        "Get-CimInstance Win32_Process | "
        "Select-Object ProcessId,ParentProcessId,Name,CommandLine,WorkingSetSize,PageFileUsage,CreationDate | "
        "ConvertTo-Json -Depth 3"
    )
    try:
        proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=30)
        if proc.returncode != 0 or not proc.stdout.strip():
            return []
        data = json.loads(proc.stdout)
        if isinstance(data, dict):
            data = [data]
    except Exception:  # noqa: BLE001
        return []
    rows = []
    for item in data:
        rows.append({
            "pid": int(item.get("ProcessId") or 0),
            "ppid": int(item.get("ParentProcessId") or 0),
            "name": str(item.get("Name") or ""),
            "cmdline": str(item.get("CommandLine") or ""),
            "rss_mb": round(float(item.get("WorkingSetSize") or 0) / (1024 * 1024), 3),
            "private_bytes_mb": round(float(item.get("PageFileUsage") or 0) / 1024, 3),
            "create_time": str(item.get("CreationDate") or ""),
        })
    return rows
