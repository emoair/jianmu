from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


PROFILE_NAME = "staged_opt_in_function_array_recursion_v1_0_7"
OPT_IN_FLAG = "enable_staged_opt_in_v1_0_7"

SUPPORTED_SUBSETS: Tuple[str, ...] = (
    "function",
    "array",
    "function_array",
    "structured_recursion",
)

POSITIVE_CATEGORIES: Tuple[str, ...] = (
    "function",
    "array",
    "function_array",
    "structured_recursion",
    "mixed",
    "opt_in_rollback",
    "replay_sample",
)

NEGATIVE_CATEGORIES: Tuple[str, ...] = (
    "default_no_opt_in_blocking",
    "malformed_opt_in_blocking",
    "disabled_profile_blocking",
    "unknown_policy_rejection",
    "unsupported_function_shape_rejection",
    "unsupported_array_shape_rejection",
    "unsupported_recursion_shape_rejection",
    "pointer_heavy_boundary_rejection",
    "malloc_free_boundary_rejection",
    "file_io_boundary_rejection",
    "multifile_boundary_rejection",
    "production_promotion_rejection",
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
class ControlledOptInSupportConfig:
    profile_name: str = PROFILE_NAME
    workers: int = 16
    compiler_workers: int = 16
    negative_validation_events: int = 50_000
    positive_validation_events: int = 50_000
    minimum_real_compiler_invocations: int = 40_000
    no_model_training: bool = True
    no_weight_update: bool = True
    explicit_opt_in_required: bool = True
    trace_writer_mode: str = "sharded"
    temp_dir_mode: str = "per_sample"
    accounting_lock: bool = True

    def negative_targets(self) -> Dict[str, int]:
        return {
            "default_no_opt_in_blocking": 10_000,
            "malformed_opt_in_blocking": 5_000,
            "disabled_profile_blocking": 5_000,
            "unknown_policy_rejection": 5_000,
            "unsupported_function_shape_rejection": 5_000,
            "unsupported_array_shape_rejection": 5_000,
            "unsupported_recursion_shape_rejection": 5_000,
            "pointer_heavy_boundary_rejection": 3_000,
            "malloc_free_boundary_rejection": 3_000,
            "file_io_boundary_rejection": 3_000,
            "multifile_boundary_rejection": 3_000,
            "production_promotion_rejection": 3_000,
        }

    def positive_targets(self) -> Dict[str, int]:
        return {
            "function": 10_000,
            "array": 10_000,
            "function_array": 10_000,
            "structured_recursion": 8_000,
            "mixed": 12_000,
            "opt_in_rollback": 5_000,
            "replay_sample": 5_000,
        }
