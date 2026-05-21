from __future__ import annotations

from collections import Counter
from typing import Dict, List

from jianmu.self_learning.datasets.boundary_labels import BoundaryLabel


CURRICULUM_STAGES = [
    ("stage_0_supported_core", [BoundaryLabel.CURRENT_SUPPORTED.value]),
    ("stage_1_hard_reject", [BoundaryLabel.CURRENT_SUPPORTED.value, BoundaryLabel.HARD_OOD.value]),
    (
        "stage_2_trap_boundary",
        [BoundaryLabel.CURRENT_SUPPORTED.value, BoundaryLabel.HARD_OOD.value, BoundaryLabel.TRUE_FALSE_ACCEPT_TRAP.value],
    ),
    (
        "stage_3_future_domain_isolation",
        [
            BoundaryLabel.CURRENT_SUPPORTED.value,
            BoundaryLabel.HARD_OOD.value,
            BoundaryLabel.TRUE_FALSE_ACCEPT_TRAP.value,
            BoundaryLabel.FUTURE_DOMAIN_CANDIDATE.value,
        ],
    ),
    (
        "stage_4_near_ood_audit",
        [
            BoundaryLabel.CURRENT_SUPPORTED.value,
            BoundaryLabel.HARD_OOD.value,
            BoundaryLabel.TRUE_FALSE_ACCEPT_TRAP.value,
            BoundaryLabel.FUTURE_DOMAIN_CANDIDATE.value,
            BoundaryLabel.NEAR_OOD_GENERALIZATION_CANDIDATE.value,
        ],
    ),
    (
        "stage_5_mixed_boundary_stress",
        [label.value for label in BoundaryLabel],
    ),
]


def build_boundary_curriculum(samples: List[Dict]) -> Dict:
    schedule = []
    for order, (name, labels) in enumerate(CURRICULUM_STAGES):
        stage_rows = [row for row in samples if row.get("boundary_label") in labels]
        schedule.append(
            {
                "stage": name,
                "order": order,
                "included_boundary_labels": labels,
                "sample_count": len(stage_rows),
                "stage_boundary_distribution": dict(Counter(row.get("boundary_label") for row in stage_rows)),
                "stage_expected_actions": dict(Counter(row.get("expected_action") for row in stage_rows)),
            }
        )
    return {
        "curriculum_stage_count": len(schedule),
        "stages": schedule,
        "stage_sample_counts": {row["stage"]: row["sample_count"] for row in schedule},
    }
