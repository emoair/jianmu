from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


STILL_NOT_PROVEN_MIRROR: Tuple[str, ...] = (
    "production function support completed",
    "production array support completed",
    "production recursion support completed",
    "RedQueen autonomous governance completed",
    "true 8h RedQueen stability rerun after time repair",
    "arbitrary project parsing",
    "formal Turing completeness proof",
    "solved program synthesis",
    "production readiness",
    "natural language layer completed",
)


@dataclass(frozen=True)
class RedQueenTruthGateConfig:
    reject_old_v1_0_8_6_8h_claim: bool = True
    require_time_integrity_repair: bool = True
    forbid_default_profile_change: bool = True
    forbid_real_promotion: bool = True

