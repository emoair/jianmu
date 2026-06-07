from __future__ import annotations

from typing import Any, Dict

from jianmu.self_learning.branchchain.branch_types import BranchDecision, BranchPath
from jianmu.self_learning.darwinforge.atomic_synthesis import AtomicSynthesis
from jianmu.self_learning.darwinforge.candidate import CandidateGenome


POLICIES = [
    "canonical_function_targetir",
    "canonical_array_targetir",
    "canonical_function_array_targetir",
    "canonical_structured_recursion_targetir",
]


def reaudit_atomic_policies() -> Dict[str, Any]:
    synth = AtomicSynthesis()
    accepted = {}
    for idx, policy in enumerate(POLICIES):
        phenotype = synth.synthesize(_genome(policy), {"signed_numbers": [idx + 5]})
        accepted[policy] = bool(
            phenotype.c_program
            and phenotype.expected_output_pred
            and phenotype.target_ir_canonical
            and "experimental_active_path=true" in phenotype.target_ir_canonical
            and "production_supported=false" in phenotype.target_ir_canonical
        )
    unknown = synth.synthesize(_genome("canonical_unknown_targetir"), {"signed_numbers": [7]})
    arithmetic = synth.synthesize(_genome("canonical_arithmetic_targetir", arithmetic=True), {"signed_numbers": [1, 2], "operator_sequence": "+"})
    return {
        "accepted": accepted,
        "unknown_policy_rejected": unknown.failure_reason == "unsupported_target_builder",
        "arithmetic_regression_path_confirmed": bool(arithmetic.c_program and "printf" in arithmetic.c_program and arithmetic.expected_output_pred == "3\n"),
        "atomic_policy_bridge_confirmed": all(accepted.values()) and unknown.failure_reason == "unsupported_target_builder",
    }


def _genome(policy: str, arithmetic: bool = False) -> CandidateGenome:
    decisions = []
    if arithmetic:
        decisions = [
            BranchDecision("support_gate", ["supported"], "supported", 100, "test", {}),
            BranchDecision("arithmetic_family", ["binary"], "binary", 100, "test", {}),
            BranchDecision("structure_policy", ["binary_operation"], "binary_operation", 100, "test", {}),
        ]
    return CandidateGenome("reaudit", BranchPath(decisions=decisions), [], "", policy)
