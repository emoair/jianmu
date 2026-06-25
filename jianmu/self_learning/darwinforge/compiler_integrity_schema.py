from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


STILL_NOT_PROVEN_COMPILER_INTEGRITY: Tuple[str, ...] = (
    "v1.0.8.8 true backend compiler invocation claim, unless verified",
    "production function support completed",
    "production array support completed",
    "production recursion support completed",
    "RedQueen autonomous governance completed",
    "production readiness",
    "formal Turing completeness proof",
    "solved program synthesis",
    "natural language layer completed",
)


@dataclass(frozen=True)
class BackendValidationConfig:
    events: int = 30_000
    minimum_backend_cl_invocations: int = 15_000
    minimum_backend_link_invocations: int = 15_000
    minimum_backend_exe_runs: int = 15_000
    workers: int = 16
    compiler_workers: int = 16
    replay_samples: int = 1_000
    replay_minimum_samples: int = 500


BACKEND_POLICIES: Tuple[str, ...] = (
    "arithmetic",
    "function",
    "array",
    "function_array",
    "structured_recursion",
    "mixed",
    "mirror_lane_swap",
    "frozen_mutation_negative",
    "unsupported_boundary_negative",
)

