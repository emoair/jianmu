from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RedQueenAllocatorConfig:
    base_weight: float = 1.0
    alpha: float = 3.0
    min_weight: float = 0.25
    max_weight: float = 5.0


@dataclass(frozen=True)
class RedQueenDryRunConfig:
    events: int = 20_000
    workers: int = 16
    compiler_workers: int = 16
