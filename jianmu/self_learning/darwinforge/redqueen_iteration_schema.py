from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from jianmu.self_learning.darwinforge.architecture_finalization_schema import PROFILE_NAME, STILL_NOT_PROVEN


ITERATION_CATEGORIES: Tuple[str, ...] = (
    "function",
    "array",
    "function_array",
    "structured_recursion",
    "mixed",
    "default_blocking",
    "unsupported_boundary",
    "rollback",
    "replay",
)

BASE_EVENT_DISTRIBUTION: Dict[str, int] = {
    "function": 10_000,
    "array": 8_000,
    "function_array": 10_000,
    "structured_recursion": 8_000,
    "mixed": 12_000,
    "default_blocking": 4_000,
    "unsupported_boundary": 4_000,
    "rollback": 2_000,
    "replay": 2_000,
}

STILL_NOT_PROVEN_ITERATION: Tuple[str, ...] = tuple(STILL_NOT_PROVEN) + (
    "RedQueen autonomous governance completed",
)


@dataclass(frozen=True)
class RedQueenIterationConfig:
    profile_name: str = PROFILE_NAME
    iteration_index: int = 1
    iteration_events: int = 60_000
    minimum_real_compiler_invocations: int = 40_000
    workers: int = 16
    compiler_workers: int = 16
    require_plan_follow_rate: float = 0.95
    no_model_training: bool = True
    no_weight_update: bool = True
    explicit_opt_in_required: bool = True
