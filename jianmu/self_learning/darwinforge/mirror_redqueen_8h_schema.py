from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


STILL_NOT_PROVEN_MIRROR_8H: Tuple[str, ...] = (
    "production function support completed",
    "production array support completed",
    "production recursion support completed",
    "RedQueen autonomous governance completed",
    "arbitrary project parsing",
    "formal Turing completeness proof",
    "solved program synthesis",
    "production readiness",
    "natural language layer completed",
)


@dataclass(frozen=True)
class MirrorRedQueen8hConfig:
    planned_wall_clock_hours: float = 8.0
    max_runtime_hours: float = 8.0
    hard_stop_hours: float = 8.5
    cycles: int = 8
    cycle_min_hours: float = 1.0
    target_events: int = 260_000
    minimum_events: int = 160_000
    minimum_real_compiler_invocations: int = 110_000
    workers: int = 16
    compiler_workers: int = 16
    heartbeat_interval_seconds: int = 300
    heartbeat_interval_events: int = 10_000


CYCLE_DESIGNS: Tuple[dict, ...] = (
    {"cycle_index": 0, "label": "baseline", "mode": "LANE_A_ACTIVE_LANE_B_FROZEN", "disagreement": 0.0, "attack": False},
    {"cycle_index": 1, "label": "lane_swap_b_active", "mode": "LANE_B_ACTIVE_LANE_A_FROZEN", "disagreement": 0.0, "attack": False},
    {"cycle_index": 2, "label": "mirror_disagreement_injected", "mode": "LANE_B_ACTIVE_LANE_A_FROZEN", "disagreement": 0.12, "attack": False},
    {"cycle_index": 3, "label": "redqueen_response", "mode": "LANE_B_ACTIVE_LANE_A_FROZEN", "disagreement": 0.10, "attack": False},
    {"cycle_index": 4, "label": "lane_swap_a_active", "mode": "LANE_A_ACTIVE_LANE_B_FROZEN", "disagreement": 0.04, "attack": False},
    {"cycle_index": 5, "label": "both_frozen_review_only", "mode": "BOTH_FROZEN_REVIEW_ONLY", "disagreement": 0.02, "attack": False},
    {"cycle_index": 6, "label": "frozen_mutation_and_simultaneous_active_attack", "mode": "LANE_A_ACTIVE_LANE_B_FROZEN", "disagreement": 0.08, "attack": True},
    {"cycle_index": 7, "label": "final_clean_annealing", "mode": "LANE_A_ACTIVE_LANE_B_FROZEN", "disagreement": 0.0, "attack": False},
)

