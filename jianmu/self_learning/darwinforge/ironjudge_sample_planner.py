from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.forgefrontier_function_array_generator import iter_forgefrontier_dataset


def plan_ironjudge_samples(forgefrontier_dataset_dir: str | Path, completed_hashes: Iterable[str], limit: int, seed: int = 112) -> Dict[str, Any]:
    completed = set(completed_hashes)
    positives: Dict[str, List[Dict[str, Any]]] = {
        "experimental_pure_function": [],
        "experimental_fixed_array": [],
        "experimental_function_array": [],
        "boundary_negative": [],
        "near_ood": [],
    }
    for row in iter_forgefrontier_dataset(forgefrontier_dataset_dir):
        sample_hash = sample_id_hash(row["id"])
        if sample_hash in completed:
            continue
        row = dict(row)
        row["sample_id_hash"] = sample_hash
        category = str(row.get("category", ""))
        status = str(row.get("support_status", ""))
        if status == "experimental_supported_function" and "pure_function" in category:
            positives["experimental_pure_function"].append(row)
        elif status == "experimental_supported_array" and "fixed_array" in category:
            positives["experimental_fixed_array"].append(row)
        elif status == "experimental_supported_function_array":
            positives["experimental_function_array"].append(row)
        elif status in {"future_domain", "unsupported", "trap", "hard_ood", "review"}:
            positives["boundary_negative"].append(row)
        else:
            positives["near_ood"].append(row)
        if sum(len(v) for v in positives.values()) >= limit * 2:
            break
    quotas = {
        "experimental_pure_function": max(1, int(limit * 0.15)),
        "experimental_fixed_array": max(1, int(limit * 0.15)),
        "experimental_function_array": max(1, int(limit * 0.10)),
        "boundary_negative": max(0, int(limit * 0.10)),
        "near_ood": max(0, int(limit * 0.05)),
    }
    # The remaining 45% bounded-control contribution is supplied by previous
    # v0.9.18 RedQueen IronJudge traces or by the v0.9.17 compiler corpus.
    rows: List[Dict[str, Any]] = []
    for bucket, quota in quotas.items():
        rows.extend(positives[bucket][:quota])
    rows = _unique(rows, limit)
    return {"planned_rows": rows, "sample_mix_target": quotas | {"previous_bounded_control": int(limit * 0.45)}, "sample_mix_actual": _mix(rows), "duplicate_sample_hash_count": len(rows) - len({row["sample_id_hash"] for row in rows})}


def sample_id_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _unique(rows: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    seen = set()
    result = []
    for row in rows:
        if row["sample_id_hash"] in seen:
            continue
        seen.add(row["sample_id_hash"])
        result.append(row)
        if len(result) >= limit:
            break
    return result


def _mix(rows: List[Dict[str, Any]]) -> Dict[str, int]:
    result: Dict[str, int] = {}
    for row in rows:
        status = str(row.get("support_status"))
        category = str(row.get("category"))
        if status.startswith("experimental"):
            key = category
        else:
            key = status
        result[key] = result.get(key, 0) + 1
    return result
