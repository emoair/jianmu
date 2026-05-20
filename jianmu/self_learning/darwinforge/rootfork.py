from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class ForkPointRecord:
    sample_id: str
    fork_layer: str
    fork_reason: str
    stable_prefix: List[List[str]]
    correct_option_at_fork: Optional[str]
    score_gap: float
    target_option_rank: Optional[int]

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


@dataclass
class RootForkMetrics:
    path_forcing_exact_match_rate: float = 0.0
    global_correct_targetir_in_beam_rate: float = 0.0
    global_candidate_space_failure_rate: float = 0.0
    teacher_subbeam_correct_targetir_rate: float = 0.0
    seeded_free_subbeam_correct_targetir_rate: float = 0.0
    subbeam_rescue_rate: float = 0.0
    rescued_sample_count: int = 0
    path_prior_seed_count: int = 0
    branch_neuron_updated_count: int = 0
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def make_fork_point_record(sample_id: str, fork_point: Dict) -> ForkPointRecord:
    return ForkPointRecord(
        sample_id=sample_id,
        fork_layer=fork_point.get("fork_layer"),
        fork_reason=fork_point.get("fork_reason"),
        stable_prefix=list(fork_point.get("stable_prefix", [])),
        correct_option_at_fork=fork_point.get("correct_option_at_fork"),
        score_gap=fork_point.get("score_gap", 0),
        target_option_rank=fork_point.get("target_option_rank"),
    )
