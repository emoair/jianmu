from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


LONGHAUL_CATEGORIES: Tuple[str, ...] = (
    "default_blocking",
    "malformed_opt_in_blocking",
    "arithmetic",
    "function",
    "array",
    "function_array",
    "structured_recursion",
    "mixed",
    "opt_out_rollback",
    "post_rollback_default_blocking",
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
class ControlledOptInLonghaulConfig:
    profile_name: str = "staged_opt_in_function_array_recursion_v1_0_7"
    wall_clock_min_hours: float = 8.0
    max_runtime_hours: float = 8.0
    hard_stop_hours: float = 8.5
    workers: int = 16
    compiler_workers: int = 16
    trace_writer_mode: str = "sharded"
    temp_dir_mode: str = "per_sample"
    accounting_lock: bool = True
    replay_samples: int = 5000
    replay_minimum_required: int = 2000
    rollback_cycles: int = 500
    samples_per_rollback_cycle: int = 5
    target_real_validation_events: int = 270000
    minimum_real_validation_events: int = 120000
    minimum_real_compiler_invocations: int = 90000
    minimum_unique_compile_units: int = 9896
    target_unique_compile_units: int = 12000
    minimum_source_sha256_unique: int = 9896
    target_source_sha256_unique: int = 12000

    def target_counts(
        self,
        default_blocking_target: int = 20000,
        malformed_opt_in_blocking_target: int = 10000,
        arithmetic_target: int = 30000,
        function_target: int = 35000,
        array_target: int = 35000,
        function_array_target: int = 35000,
        recursion_target: int = 25000,
        mixed_target: int = 40000,
        opt_out_rollback_target: int = 25000,
        post_rollback_default_blocking_target: int = 15000,
    ) -> Dict[str, int]:
        return {
            "default_blocking": default_blocking_target,
            "malformed_opt_in_blocking": malformed_opt_in_blocking_target,
            "arithmetic": arithmetic_target,
            "function": function_target,
            "array": array_target,
            "function_array": function_array_target,
            "structured_recursion": recursion_target,
            "mixed": mixed_target,
            "opt_out_rollback": opt_out_rollback_target,
            "post_rollback_default_blocking": post_rollback_default_blocking_target,
        }
