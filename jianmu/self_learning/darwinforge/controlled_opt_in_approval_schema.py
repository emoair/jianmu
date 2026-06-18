from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


PROFILE_NAME = "staged_opt_in_function_array_recursion_v1_0_7"

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
class ApprovalGateConfig:
    profile_name: str = PROFILE_NAME
    workers: int = 16
    positive_samples: int = 1000
    negative_samples: int = 1000
    rollback_samples: int = 300
    policy_path_samples: int = 300
    stdout_samples: int = 1000
    unsupported_rejection_samples: int = 500
    default_blocking_samples: int = 500
    no_model_training: bool = True
    no_weight_update: bool = True
    explicit_opt_in_required: bool = True
