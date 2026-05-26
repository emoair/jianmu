from __future__ import annotations

from typing import Any, Dict, List


REQUIRED_STAGES = [
    "variable_declaration",
    "assignment_sequence",
    "multi_variable_sequence",
    "if_else_basic",
    "if_else_nested",
    "bounded_for_loop",
    "bounded_while_with_fuel",
    "nested_bounded_control",
    "boundary_rejection",
    "future_near_ood_quarantine",
    "mixed_final",
]


def build_turing_substrate_curriculum_schedule() -> Dict[str, Any]:
    stages: List[Dict[str, Any]] = []
    for name in REQUIRED_STAGES:
        boundary = name in {"boundary_rejection", "future_near_ood_quarantine", "mixed_final"}
        stages.append({
            "stage_name": name,
            "included_categories": ["current_supported_turing_substrate"] if not boundary else [
                "current_supported_turing_substrate",
                "unsupported_program_boundary",
                "true_false_accept_trap",
                "future_domain_candidate",
                "near_ood_program",
                "hard_ood",
            ],
            "included_features": _features_for_stage(name),
            "target_supported_ratio": 0.75 if not boundary else 0.35,
            "target_ood_ratio": 0.25 if not boundary else 0.65,
            "nutrient_pressure": "reward compiler-verified bounded state updates",
            "toxicity_pressure": "penalize unsafe, unbounded, or future-domain false accepts",
            "promotion_allowed": False,
            "real_promotion_allowed": False,
            "expected_exit_condition": "auditable sample coverage only; no model-training claim",
        })
    return {"dataset_version": "v0.9.6", "stages": stages}


def _features_for_stage(stage: str) -> List[str]:
    mapping = {
        "variable_declaration": ["has_variable_decl"],
        "assignment_sequence": ["has_variable_decl", "has_assignment", "has_sequence"],
        "multi_variable_sequence": ["has_variable_decl", "has_assignment", "has_sequence"],
        "if_else_basic": ["has_if_else"],
        "if_else_nested": ["has_if_else", "has_nested_control"],
        "bounded_for_loop": ["has_for_loop"],
        "bounded_while_with_fuel": ["has_while_loop"],
        "nested_bounded_control": ["has_nested_control", "has_for_loop", "has_if_else"],
        "boundary_rejection": ["unsupported_boundaries"],
        "future_near_ood_quarantine": ["future_domain", "near_ood"],
        "mixed_final": ["mixed_supported_and_boundary"],
    }
    return mapping[stage]
