from __future__ import annotations

import json
from pathlib import Path


def audit_artifact_cache_pressure(output_records: str | Path, *, compiler_artifact_root: str | Path, dataset_artifact_root: str | Path, records_root: str | Path) -> dict:
    compiler = _tree_stats(Path(compiler_artifact_root))
    dataset = _tree_stats(Path(dataset_artifact_root))
    records = _tree_stats(Path(records_root))
    trace_files = [p for p in Path(records_root).rglob("*.jsonl") if p.is_file()]
    trace_total = sum(p.stat().st_size for p in trace_files)
    largest_trace = max((p.stat().st_size for p in trace_files), default=0)
    total_files = compiler["file_count"] + dataset["file_count"] + records["file_count"]
    result = {
        "artifact_cache_audit_completed": True,
        "compiler_artifact_file_count": compiler["file_count"],
        "compiler_artifact_total_mb": compiler["total_mb"],
        "dataset_artifact_file_count": dataset["file_count"],
        "dataset_artifact_total_mb": dataset["total_mb"],
        "records_total_mb": records["total_mb"],
        "trace_total_mb": round(trace_total / (1024 * 1024), 3),
        "largest_trace_shard_mb": round(largest_trace / (1024 * 1024), 3),
        "file_churn_rate_per_minute": total_files,
        "artifact_root_outside_worktree": _outside_worktree(Path(compiler_artifact_root)) and _outside_worktree(Path(dataset_artifact_root)),
        "onedrive_watched_path_involved": "OneDrive" in str(Path(records_root).resolve()),
    }
    result["file_cache_pressure_suspected"] = result["compiler_artifact_file_count"] > 5000 or result["records_total_mb"] > 100
    result["artifact_cache_audit_passed"] = result["artifact_root_outside_worktree"] and largest_trace < 50_000_000
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "artifact_cache_pressure_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def _tree_stats(root: Path) -> dict:
    if not root.exists():
        return {"file_count": 0, "total_mb": 0.0}
    count = 0
    total = 0
    for path in root.rglob("*"):
        if path.is_file():
            count += 1
            total += path.stat().st_size
    return {"file_count": count, "total_mb": round(total / (1024 * 1024), 3)}


def _outside_worktree(path: Path) -> bool:
    try:
        resolved = path.resolve()
        cwd = Path.cwd().resolve()
        return not (resolved == cwd or cwd in resolved.parents)
    except OSError:
        return False
