from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


PROFILE_NAME = "staged_opt_in_function_array_recursion_v1_0_7"

POLICY_BY_KIND: Dict[str, str] = {
    "arithmetic": "canonical_arithmetic_targetir",
    "function": "canonical_function_targetir",
    "array": "canonical_array_targetir",
    "function_array": "canonical_function_array_targetir",
    "structured_recursion": "canonical_structured_recursion_targetir",
    "mixed": "mixed_extended_ir_path",
    "default_blocking": "default_profile_blocking_check",
    "opt_out_rollback": "opt_out_rollback_check",
}

OPT_IN_POLICIES: Tuple[str, ...] = (
    "canonical_function_targetir",
    "canonical_array_targetir",
    "canonical_function_array_targetir",
    "canonical_structured_recursion_targetir",
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
class StagedOptInProfileConfig:
    profile_name: str = PROFILE_NAME
    explicitly_opt_in: bool = True
    default_profile: bool = False
    default_profile_unchanged: bool = True
    real_promotion_enabled: bool = False
    user_facing_enabled: bool = False
    official_release_enabled: bool = False
    production_support_claim_enabled: bool = False
    opt_in_enabled_only_by_explicit_flag: bool = True
    opt_out_supported: bool = True
    rollback_required: bool = True
    audit_trace_required: bool = True
    compiler_validation_required: bool = True
    production_supported: bool = False
    staged_opt_in_candidate: bool = True
    experimental_active_bridge: bool = True
    workers: int = 16
    compiler_workers: int = 16
    trace_writer_mode: str = "sharded"
    temp_dir_mode: str = "per_sample"
    accounting_lock: bool = True
    enabled_policies: Tuple[str, ...] = OPT_IN_POLICIES
    disabled_policies: Tuple[str, ...] = ()

    def target_counts(
        self,
        default_blocking_target: int = 5000,
        arithmetic_target: int = 15000,
        function_target: int = 20000,
        array_target: int = 20000,
        function_array_target: int = 20000,
        recursion_target: int = 15000,
        mixed_target: int = 25000,
        opt_out_rollback_target: int = 10000,
    ) -> Dict[str, int]:
        return {
            "default_blocking": default_blocking_target,
            "arithmetic": arithmetic_target,
            "function": function_target,
            "array": array_target,
            "function_array": function_array_target,
            "structured_recursion": recursion_target,
            "mixed": mixed_target,
            "opt_out_rollback": opt_out_rollback_target,
        }

    def claim_boundary(self) -> Dict[str, object]:
        return {
            "production_function_support_completed": False,
            "production_array_support_completed": False,
            "production_recursion_support_completed": False,
            "ready_for_official_release": False,
            "production_ready": False,
            "official_release_ready": False,
            "allowed_positive_claim": "ready_for_controlled_opt_in_support_review",
            "still_not_proven": list(STILL_NOT_PROVEN),
        }
