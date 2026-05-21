from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from jianmu.self_learning.datasets.symbol_grounding import load_symbol_grounding_split


def split_hash(samples: Iterable[Dict]) -> str:
    digest = hashlib.sha256()
    for sample in samples:
        digest.update(json.dumps({
            "sample_id": sample.get("sample_id"),
            "input_text": sample.get("input_text"),
            "split": sample.get("split"),
        }, ensure_ascii=False, sort_keys=True).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()[:16]


def compute_split_diagnostics(dataset_dir: str | Path, requested_limits: Dict[str, Optional[int]], actual_samples: Dict[str, List[Dict] | int]) -> Dict:
    dataset_dir = Path(dataset_dir)
    train_all = load_symbol_grounding_split(dataset_dir, "train")
    eval_all = load_symbol_grounding_split(dataset_dir, "eval")
    ood_all = load_symbol_grounding_split(dataset_dir, "ood")

    def _actual_count(key: str) -> int:
        value = actual_samples.get(key, [])
        return int(value) if isinstance(value, int) else len(value)

    actual_train = _actual_count("train")
    actual_eval = _actual_count("eval")
    actual_ood = _actual_count("ood")
    req_train = requested_limits.get("train")
    req_eval = requested_limits.get("eval")
    req_ood = requested_limits.get("ood")

    mismatch = (req_train is not None and actual_train < req_train) or (req_eval is not None and actual_eval < req_eval) or (req_ood is not None and actual_ood < req_ood)
    if mismatch and (actual_train == min(req_train or len(train_all), len(train_all)) and actual_eval == min(req_eval or len(eval_all), len(eval_all)) and actual_ood == min(req_ood or len(ood_all), len(ood_all))):
        reason = "dataset_capacity"
    elif mismatch:
        reason = "loader_policy"
    else:
        reason = "none"

    return {
        "requested_train_limit": req_train,
        "requested_eval_limit": req_eval,
        "requested_ood_limit": req_ood,
        "actual_train_count": actual_train,
        "actual_eval_count": actual_eval,
        "actual_ood_count": actual_ood,
        "dataset_capacity_train": len(train_all),
        "dataset_capacity_eval": len(eval_all),
        "dataset_capacity_ood": len(ood_all),
        "split_hash_train": split_hash(train_all[:actual_train]),
        "split_hash_eval": split_hash(eval_all[:actual_eval]),
        "split_hash_ood": split_hash(ood_all[:actual_ood]),
        "reason_for_limit_mismatch": reason,
    }
