from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


LANE_A_ACTIVE_LANE_B_FROZEN = "LANE_A_ACTIVE_LANE_B_FROZEN"
LANE_B_ACTIVE_LANE_A_FROZEN = "LANE_B_ACTIVE_LANE_A_FROZEN"
BOTH_FROZEN_REVIEW_ONLY = "BOTH_FROZEN_REVIEW_ONLY"
INVALID_BOTH_ACTIVE = "INVALID_BOTH_ACTIVE"

MIRROR_TERMS: Tuple[str, ...] = (
    "mirror",
    "MirrorForge",
    "alternating",
    "alternate",
    "freeze",
    "frozen",
    "active_lane",
    "frozen_lane",
    "co_symbiosis",
    "cosymbiosis",
    "symbiosis",
    "twin",
    "shadow",
    "dual_lane",
    "lane_swap",
    "freeze_schedule",
    "mirror_disagreement",
    "mirror_feedback",
    "mirror_metrics",
)


@dataclass(frozen=True)
class MirrorRuntimeProbeConfig:
    events: int = 30_000
    minimum_real_compiler_invocations: int = 15_000
    phases: int = 4
    workers: int = 16
    compiler_workers: int = 16
    explicit_opt_in_required: bool = True

