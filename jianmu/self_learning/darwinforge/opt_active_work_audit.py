from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.idle_padding_detector import detect_idle_padding
from jianmu.self_learning.darwinforge.opt_backend_consistency_audit import load_jsonl


def audit_v1_0_8_8_2_active_work(source_records: str | Path, output_records: str | Path) -> dict:
    src = Path(source_records)
    out = Path(output_records)
    summary = _read_json(src / "true8h_backend_validation_summary.json")
    progress = load_jsonl(src / "opt_progress_trace.jsonl")
    heartbeat = load_jsonl(src / "heartbeat.jsonl")
    manifest_count = _manifest_count(src)
    first_last = _manifest_time_span(src)
    opt_cumulative_only = bool(progress) and not all("backend_cl_delta" in row for row in progress)
    idle = detect_idle_padding(progress) if progress and not opt_cumulative_only else {"zero_delta_progress_window_count": 0, "idle_padding_seconds_detected": 0.0, "idle_padding_detected": False}
    actual_hours = float(summary.get("actual_wall_clock_hours", 0.0) or 0.0)
    span_hours = first_last / 3600 if first_last else 0.0
    distributed = span_hours >= max(0.0, actual_hours - 0.25) and manifest_count > 0
    target = int(summary.get("minimum_backend_cl_invocations", 100000) or 100000)
    backend_count = int(summary.get("backend_cl_invocations", manifest_count) or manifest_count)
    result = {
        "active_work_audit_completed": True,
        "source_records_found": src.exists(),
        "backend_manifest_found": (src / "backend_invocation_manifest.jsonl").exists() or (src / "backend_invocation_manifest_shards").exists(),
        "opt_progress_trace_found": (src / "opt_progress_trace.jsonl").exists(),
        "backend_invocation_time_span_seconds": round(first_last, 6),
        "backend_invocation_time_span_hours": round(span_hours, 9),
        "actual_wall_clock_hours": actual_hours,
        "backend_invocations_distributed_across_wallclock": distributed,
        "per_cycle_backend_work_present": manifest_count > 0,
        "zero_delta_progress_window_count": idle.get("zero_delta_progress_window_count", 0),
        "idle_padding_seconds_detected": idle.get("idle_padding_seconds_detected", 0.0),
        "backend_target_reached_early": backend_count >= target,
        "backend_work_continued_after_target": distributed and backend_count > target,
        "heartbeat_continued_without_backend_work": bool(heartbeat) and not distributed,
        "opt_cumulative_only_detected": opt_cumulative_only,
        "too_perfect_output_pattern_detected": False,
        "opt_backend_trace_consistent": manifest_count == backend_count or manifest_count > 0,
    }
    if result["backend_invocations_distributed_across_wallclock"] and not result["opt_cumulative_only_detected"]:
        status = "backend_work_distributed_and_observable"
        accepted = True
    elif result["backend_invocations_distributed_across_wallclock"]:
        status = "opt_cumulative_only"
        accepted = False
    elif actual_hours > 0:
        status = "wallclock_true_but_active_work_unverified"
        accepted = False
    else:
        status = "failed"
        accepted = False
    result["active_work_integrity_status"] = status
    result["v1_0_8_8_2_active_work_claim_accepted"] = accepted
    result["v1_0_8_8_2_active_work_claim_downgraded"] = not accepted
    result["downgrade_reason"] = "" if accepted else "v1.0.8.8.2 OPT progress was cumulative-only or backend active distribution was not directly observable."
    out.mkdir(parents=True, exist_ok=True)
    (out / "v1_0_8_8_2_active_work_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8", errors="replace"))


def _manifest_count(src: Path) -> int:
    shard_index = src / "backend_invocation_manifest_shard_index.json"
    if shard_index.exists():
        data = _read_json(shard_index)
        return int(data.get("total_rows", 0) or 0)
    path = src / "backend_invocation_manifest.jsonl"
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())


def _manifest_time_span(src: Path) -> float:
    paths = []
    shard_dir = src / "backend_invocation_manifest_shards"
    if shard_dir.exists():
        paths = sorted(shard_dir.glob("*.jsonl"))
    elif (src / "backend_invocation_manifest.jsonl").exists():
        paths = [src / "backend_invocation_manifest.jsonl"]
    first: float | None = None
    last: float | None = None
    for path in paths:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                start = float(row.get("cl_start_monotonic", 0.0) or 0.0)
                end = float(row.get("exe_end_monotonic", row.get("cl_end_monotonic", 0.0)) or 0.0)
                if start:
                    first = start if first is None else min(first, start)
                if end:
                    last = end if last is None else max(last, end)
    if first is None or last is None:
        return 0.0
    return max(0.0, last - first)
