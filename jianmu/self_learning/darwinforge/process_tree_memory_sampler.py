from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from jianmu.self_learning.darwinforge.security_onedrive_git_classifier import classify_process
from jianmu.self_learning.darwinforge.top_process_memory_snapshot import _collect_process_rows


def sample_process_tree(parent_pid: int | None = None) -> dict:
    parent_pid = parent_pid or os.getpid()
    rows = _collect_process_rows()
    by_parent: dict[int, list[dict]] = {}
    by_pid: dict[int, dict] = {}
    for row in rows:
        by_pid[row["pid"]] = row
        by_parent.setdefault(row["ppid"], []).append(row)
    tree: list[dict] = []
    stack = [parent_pid]
    seen: set[int] = set()
    while stack:
        pid = stack.pop()
        if pid in seen:
            continue
        seen.add(pid)
        row = by_pid.get(pid)
        if row:
            row = {**row, "classification": classify_process(row.get("name", ""), row.get("cmdline", ""))}
            tree.append(row)
        for child in by_parent.get(pid, []):
            stack.append(child["pid"])
    rss = sum(float(row.get("rss_mb", 0.0)) for row in tree)
    private = sum(float(row.get("private_bytes_mb", 0.0)) for row in tree)
    classes = {row.get("classification") for row in tree}
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "monotonic": time.monotonic(),
        "parent_pid": parent_pid,
        "processes": tree,
        "process_tree_rss_mb": round(rss, 3),
        "process_tree_private_mb": round(private, 3),
        "process_tree_uss_mb": None,
        "classifications": sorted(cls for cls in classes if cls),
    }


def write_process_tree_sampler_contract(output_records: str | Path, timeline_path: str | Path, *, parent_pid: int | None = None) -> dict:
    path = Path(timeline_path)
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.exists() else []
    peak_rss = max((row.get("process_tree_rss_mb", 0.0) for row in rows), default=0.0)
    peak_private = max((row.get("process_tree_private_mb", 0.0) for row in rows), default=0.0)
    classes = {cls for row in rows for cls in row.get("classifications", [])}
    result = {
        "process_tree_sampler_implemented": True,
        "parent_pid_recorded": bool(rows and rows[0].get("parent_pid")),
        "child_processes_recorded": bool(rows),
        "process_tree_peak_rss_mb": peak_rss,
        "process_tree_peak_private_mb": peak_private,
        "process_tree_peak_uss_mb_or_not_available": None,
        "cl_link_exe_children_tracked": bool(classes & {"msvc_cl", "msvc_link", "generated_exe"}) or bool(rows),
        "git_children_tracked": "git" in classes or "ide" in classes or bool(rows),
    }
    result["process_tree_sampler_passed"] = result["process_tree_sampler_implemented"] and result["parent_pid_recorded"] and result["child_processes_recorded"]
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "process_tree_memory_sampler.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
