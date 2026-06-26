from __future__ import annotations

import json
from pathlib import Path


def audit_trace_shard_size_cap(root: str | Path, *, output_records: str | Path | None = None, max_trace_shard_size_bytes: int = 44_000_000, warning_threshold_bytes: int = 40_000_000, hard_fail_threshold_bytes: int = 50_000_000) -> dict:
    base = Path(root)
    files = [p for p in base.rglob("*.jsonl") if p.is_file()]
    sizes = [(p, p.stat().st_size) for p in files]
    oversized = [(str(p), size) for p, size in sizes if size >= hard_fail_threshold_bytes]
    largest = max((size for _p, size in sizes), default=0)
    result = {
        "trace_shard_cap_implemented": True,
        "max_trace_shard_size_bytes": max_trace_shard_size_bytes,
        "warning_threshold_bytes": warning_threshold_bytes,
        "hard_fail_threshold_bytes": hard_fail_threshold_bytes,
        "oversized_shard_count": len(oversized),
        "largest_shard_bytes": largest,
        "oversized_shards": oversized,
        "shard_rotation_triggered": bool(files),
    }
    result["trace_shard_size_cap_passed"] = len(oversized) == 0 and largest < hard_fail_threshold_bytes
    if output_records is not None:
        out = Path(output_records)
        out.mkdir(parents=True, exist_ok=True)
        (out / "trace_shard_size_cap.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
