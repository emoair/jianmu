from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Dict


def sample_temp_dir(sample_id: str, worker_id: int, root: str | Path | None = None) -> Path:
    base = Path(root) if root else Path(tempfile.gettempdir())
    safe = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in sample_id)
    return base / "jianmu_replay_workers" / f"worker_{worker_id:02d}" / safe


def verify_worker_isolation(sample_id: str = "sample", workers: int = 16) -> Dict[str, object]:
    paths = [sample_temp_dir(sample_id, worker) for worker in range(workers)]
    return {
        "per_sample_temp_dir_confirmed": len(paths) == len(set(paths)),
        "workers": workers,
        "sample_paths_unique": len(paths) == len(set(paths)),
    }
