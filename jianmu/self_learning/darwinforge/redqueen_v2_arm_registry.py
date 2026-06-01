from __future__ import annotations

from typing import Dict, List


ARMS = [
    "bounded_for_loop",
    "if_else_nested",
    "if_else_basic",
    "bounded_while_with_fuel",
    "nested_bounded_control",
    "multi_variable_update",
    "condition_boundary",
    "loop_bound_off_by_one",
    "wrong_top1_contrast_pairs",
    "candidate_miss_contrast_pairs",
    "boundary_preservation_negatives",
]


def build_arm_registry() -> Dict[str, List[Dict[str, object]]]:
    arms = []
    for arm in ARMS:
        arms.append({
            "arm_id": arm,
            "arm_type": "contrastive" if "contrast" in arm else ("boundary_negative" if arm == "boundary_preservation_negatives" else "causal_pattern"),
            "eligible_for_runtime_boundary": False,
            "uses_data_contract": True,
        })
    return {"arms": arms, "arm_count": len(arms)}
