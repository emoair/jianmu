from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List


def write_checkpoint(
    checkpoint_root: str | Path,
    level_name: str,
    target_total_invocations: int,
    previous_invocations_used: int,
    new_invocations_completed: int,
    completed_sample_hashes: Iterable[str],
    failed_sample_hashes: Iterable[str],
    pending_sample_hashes: Iterable[str],
    shard_paths: Iterable[str],
    completed: bool,
    partial: bool,
    partial_reason: str,
) -> Dict[str, Any]:
    checkpoint = {
        "level_name": level_name,
        "target_total_invocations": target_total_invocations,
        "previous_invocations_used": previous_invocations_used,
        "new_invocations_completed": new_invocations_completed,
        "total_invocations_completed": previous_invocations_used + new_invocations_completed,
        "completed_sample_hashes": sorted(set(completed_sample_hashes)),
        "failed_sample_hashes": sorted(set(failed_sample_hashes)),
        "pending_sample_hashes": sorted(set(pending_sample_hashes)),
        "shard_paths": list(shard_paths),
        "last_update_time": datetime.now(timezone.utc).isoformat(),
        "completed": completed,
        "partial": partial,
        "partial_reason": partial_reason,
        "resume_safe": True,
    }
    path = Path(checkpoint_root) / level_name / "checkpoint.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(checkpoint, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return checkpoint


def load_checkpoint(checkpoint_root: str | Path, level_name: str) -> Dict[str, Any] | None:
    path = Path(checkpoint_root) / level_name / "checkpoint.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def checkpoint_roundtrip(tmp_path: str | Path) -> Dict[str, Any]:
    return write_checkpoint(tmp_path, "gate_5k", 5000, 10, 5, ["a"], [], ["b"], ["trace.jsonl"], False, True, "test")
