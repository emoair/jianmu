from __future__ import annotations

from typing import Any, Dict, List


REQUIRED_STAGES = [
    "symbolic_single_op",
    "symbolic_two_op",
    "precedence",
    "parentheses",
    "negative_numbers",
    "exact_division",
    "boundary_rejection",
    "trap_rejection",
    "future_near_ood_quarantine",
    "mixed_final",
]


def build_arithmetic_curriculum_schedule() -> Dict[str, Any]:
    stages: List[Dict[str, Any]] = []
    for name in REQUIRED_STAGES:
        if name in {"boundary_rejection", "trap_rejection", "future_near_ood_quarantine"}:
            supported_ratio = 0.2
            ood_ratio = 0.8
        else:
            supported_ratio = 0.8
            ood_ratio = 0.2
        stages.append(
            {
                "stage_name": name,
                "included_categories": _categories(name),
                "included_expression_stages": _expression_stages(name),
                "target_supported_ratio": supported_ratio,
                "target_ood_ratio": ood_ratio,
                "nutrient_pressure": "positive_on_correct_boundary_action",
                "toxicity_pressure": "toxic_on_false_supported_accept_or_false_reject",
                "promotion_allowed": False,
                "real_promotion_allowed": False,
                "expected_exit_condition": "audit counters stable; no real promotion",
            }
        )
    return {"dataset_version": "v0.9.2", "stages": stages}


def _categories(name: str) -> List[str]:
    if name == "trap_rejection":
        return ["true_false_accept_trap"]
    if name == "future_near_ood_quarantine":
        return ["future_domain_candidate", "near_ood_arithmetic"]
    if name == "boundary_rejection":
        return ["unsupported_arithmetic_boundary", "hard_ood"]
    return ["current_supported_arithmetic"]


def _expression_stages(name: str) -> List[str]:
    mapping = {
        "symbolic_single_op": ["single_op"],
        "symbolic_two_op": ["two_op_no_parentheses"],
        "precedence": ["precedence"],
        "parentheses": ["parentheses"],
        "negative_numbers": ["negative_numbers"],
        "exact_division": ["exact_division"],
    }
    return mapping.get(name, ["mixed_boundary"])
