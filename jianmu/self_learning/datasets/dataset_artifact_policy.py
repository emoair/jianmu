from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class DatasetArtifactPolicy:
    max_file_size_mb_for_git: int = 50
    prefer_shards_above_mb: int = 40
    shard_target_size_mb: int = 25
    allow_large_jsonl_commit: bool = False
    allow_lfs_hint: bool = True


def check_dataset_artifacts(dataset_dir: str | Path, policy: DatasetArtifactPolicy | None = None) -> Dict:
    policy = policy or DatasetArtifactPolicy()
    dataset_dir = Path(dataset_dir)
    oversized = []
    should_shard = []
    for path in dataset_dir.rglob("*.jsonl"):
        size_mb = path.stat().st_size / (1024 * 1024)
        row = {"path": str(path), "size_mb": round(size_mb, 3)}
        if size_mb > policy.max_file_size_mb_for_git:
            oversized.append(row)
        if size_mb > policy.prefer_shards_above_mb:
            should_shard.append(row)
    historical = [row for row in oversized if "v0_8_5_boundary_aware" in row["path"]]
    new_oversized = [row for row in oversized if row not in historical]
    blocking = len(new_oversized) if not policy.allow_large_jsonl_commit else 0
    return {
        "oversized_file_count": len(oversized),
        "oversized_files": oversized,
        "historical_oversized_files": historical,
        "new_oversized_files": new_oversized,
        "should_shard": bool(should_shard),
        "files_recommended_for_sharding": should_shard,
        "lfs_recommended": bool(oversized) and policy.allow_lfs_hint,
        "blocking_issue_count": blocking,
        "artifact_policy_passed": blocking == 0,
        "max_file_size_mb_for_git": policy.max_file_size_mb_for_git,
        "prefer_shards_above_mb": policy.prefer_shards_above_mb,
        "shard_target_size_mb": policy.shard_target_size_mb,
    }
