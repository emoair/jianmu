from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


PROFILE_NAME = "staged_opt_in_function_array_recursion_v1_0_7"

REDQUEEN_CATEGORIES: Tuple[str, ...] = (
    "function",
    "array",
    "function_array",
    "structured_recursion",
    "mixed",
    "default_blocking",
    "unsupported_boundary",
)

STILL_NOT_PROVEN: Tuple[str, ...] = (
    "production function support completed",
    "production array support completed",
    "production recursion support completed",
    "arbitrary project parsing",
    "formal Turing completeness proof",
    "solved program synthesis",
    "production readiness",
    "natural language layer completed",
    "safe real promotion",
    "stable convergence",
    "solved OOD",
    "emergence proven",
)


@dataclass(frozen=True)
class RedQueenBootstrapConfig:
    profile_name: str = PROFILE_NAME
    workers: int = 16
    compiler_workers: int = 16
    dry_run_events: int = 20_000
    no_model_training: bool = True
    no_weight_update: bool = True
    explicit_opt_in_required: bool = True
