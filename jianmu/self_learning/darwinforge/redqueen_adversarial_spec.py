from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class RedQueenAdversarialSpec:
    spec_id: str
    target_stage: str
    pattern: str
    difficulty: int
    desired_count: int


def from_data_need_spec(data: Dict[str, object]) -> RedQueenAdversarialSpec:
    return RedQueenAdversarialSpec(
        spec_id=str(data["spec_id"]),
        target_stage=str(data["target_stage"]),
        pattern=str(data["pattern"]),
        difficulty=int(data["difficulty"]),
        desired_count=int(data["desired_count"]),
    )

