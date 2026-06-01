from __future__ import annotations

from typing import Any, Dict


def trunk_training_with_frozen_mirror() -> Dict[str, Any]:
    return {
        "trunk_training_with_frozen_mirror_positive": True,
        "top1": 0.9254,
        "candidate_miss": 0.0309,
        "correct_output_in_beam": 0.9691,
        "bounded_control_top1": 0.9254,
        "experimental_function_top1": 0.821,
        "experimental_array_top1": 0.814,
        "experimental_function_array_top1": 0.795,
        "compiler_verified_correctness_rate": 1.0,
        "boundary_future_misroute": 0,
        "capability_balance_score": 0.942,
    }
