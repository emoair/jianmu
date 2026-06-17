from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


def build_replay_shard_index(trace_pack: str | Path) -> Dict[str, Any]:
    pack = Path(trace_pack)
    shards = sorted(pack.glob("coverage_replay_policy_path_trace_*.jsonl"))
    if not shards:
        shards = sorted(pack.glob("longhaul_policy_path_trace_*.jsonl"))
    entries = [{"path": str(path), "size_bytes": path.stat().st_size} for path in shards]
    return {
        "shard_index_created": bool(entries),
        "trace_pack": str(pack),
        "shard_count": len(entries),
        "shards": entries,
        "avoids_full_rescan_per_worker": True,
    }


def read_trace_rows_from_index(index: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for shard in index.get("shards", []):
        with Path(str(shard["path"])).open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def iter_trace_rows_from_shards(paths: Iterable[str | Path]):
    for path in paths:
        with Path(path).open(encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    yield json.loads(line)
