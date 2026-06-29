from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


DATASET_CATEGORIES: Tuple[str, ...] = (
    "arithmetic",
    "function",
    "array",
    "function-array",
    "structured recursion",
    "mixed",
    "mirror lane swap",
    "frozen mutation negative",
    "unsupported boundary negative",
    "RedQueen weak-signal synthetic",
)


@dataclass(frozen=True)
class IncrementalDatasetConfig:
    target_dataset_samples: int = 500_000
    minimum_dataset_samples: int = 250_000
    train_ratio: float = 0.70
    heldout_ratio: float = 0.15
    replay_ratio: float = 0.10
    negative_boundary_ratio: float = 0.05
    shard_size: int = 50_000
    evidence_count: int = 500


def split_for_index(index: int, total: int, cfg: IncrementalDatasetConfig) -> str:
    train_end = int(total * cfg.train_ratio)
    heldout_end = train_end + int(total * cfg.heldout_ratio)
    replay_end = heldout_end + int(total * cfg.replay_ratio)
    if index < train_end:
        return "train"
    if index < heldout_end:
        return "heldout"
    if index < replay_end:
        return "replay"
    return "negative_boundary"
