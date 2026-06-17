from __future__ import annotations

from typing import Any, Dict, List


def assign_replay_shards(shard_index: Dict[str, Any], replay_workers: int = 16) -> Dict[str, Any]:
    assignments: List[Dict[str, Any]] = [{"worker_id": worker, "shards": []} for worker in range(replay_workers)]
    for index, shard in enumerate(shard_index.get("shards", [])):
        assignments[index % replay_workers]["shards"].append(shard["path"])
    return {
        "replay_workers_requested": replay_workers,
        "replay_workers_used": replay_workers,
        "replay_downgraded": False,
        "per_worker_shard_assignment": True,
        "assignments": assignments,
    }
