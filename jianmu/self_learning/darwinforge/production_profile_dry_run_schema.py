from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


PROFILE_NAME = "production_shadow_dry_run_v1_0_6"

POLICY_BY_KIND: Dict[str, str] = {
    "arithmetic": "canonical_arithmetic_targetir",
    "function": "canonical_function_targetir",
    "array": "canonical_array_targetir",
    "function_array": "canonical_function_array_targetir",
    "structured_recursion": "canonical_structured_recursion_targetir",
    "mixed": "mixed_extended_ir_path",
}

SHADOW_ENABLED_POLICIES: Tuple[str, ...] = (
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
class ProductionProfileDryRunConfig:
    profile_name: str = PROFILE_NAME
    explicitly_opt_in: bool = True
    default_profile: bool = False
    real_promotion_enabled: bool = False
    user_facing_enabled: bool = False
    release_enabled: bool = False
    production_support_claim_enabled: bool = False
    rollback_required: bool = True
    audit_trace_required: bool = True
    compiler_validation_required: bool = True
    dry_run_enabled: bool = True
    experimental_active_bridge: bool = True
    production_supported: bool = False
    workers: int = 16
    compiler_workers: int = 16
    trace_writer_mode: str = "sharded"
    temp_dir_mode: str = "per_sample"
    accounting_lock: bool = True
    enabled_policies: Tuple[str, ...] = SHADOW_ENABLED_POLICIES
    disabled_policies: Tuple[str, ...] = field(default_factory=tuple)

    def target_counts(
        self,
        arithmetic_target: int = 20_000,
        function_target: int = 20_000,
        array_target: int = 20_000,
        function_array_target: int = 20_000,
        recursion_target: int = 15_000,
        mixed_target: int = 25_000,
    ) -> Dict[str, int]:
        return {
            "arithmetic": arithmetic_target,
            "function": function_target,
            "array": array_target,
            "function_array": function_array_target,
            "structured_recursion": recursion_target,
            "mixed": mixed_target,
        }

    def claim_boundary(self) -> Dict[str, object]:
        return {
            "production_function_support_completed": False,
            "production_array_support_completed": False,
            "production_recursion_support_completed": False,
            "ready_for_official_release": False,
            "production_ready": False,
            "allowed_positive_claim": "ready_for_controlled_profile_review",
            "still_not_proven": list(STILL_NOT_PROVEN),
        }


def all_policy_kinds() -> List[str]:
    return list(POLICY_BY_KIND)
