from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class BoundaryRewardSignal:
    positive_reward: float
    toxicity: float
    neutral_signal: float
    reward_reason: str
    toxicity_reason: str
    expected_action_match: bool
    boundary_label: str
    training_usage: str

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def compute_boundary_reward(sample: Dict, candidate_result: Dict) -> BoundaryRewardSignal:
    label = sample.get("boundary_label", "unknown")
    usage = sample.get("training_usage", "unknown")
    accepted = bool(candidate_result.get("accepted_as_supported", False))
    rejected = bool(candidate_result.get("rejected", not accepted))
    exact = bool(candidate_result.get("targetir_exact_match") or candidate_result.get("output_match"))
    if label == "current_supported":
        if accepted and exact:
            return _signal(1.0, 0.0, "current_supported_correct_accept", "none", True, label, usage)
        if rejected:
            return _signal(0.0, 1.0, "none", "current_supported_false_reject", False, label, usage)
        return _signal(0.0, 0.5, "none", "current_supported_wrong_accept", False, label, usage)
    if label == "hard_ood":
        if rejected:
            return _signal(1.0, 0.0, "hard_ood_correct_reject", "none", True, label, usage)
        return _signal(0.0, 2.0, "none", "hard_ood_false_accept", False, label, usage)
    if label == "true_false_accept_trap":
        if rejected:
            return _signal(1.0, 0.0, "trap_correct_reject", "none", True, label, usage)
        return _signal(0.0, 2.5, "none", "trap_false_accept", False, label, usage)
    if label == "future_domain_candidate":
        if rejected:
            return _signal(0.2, 0.0, "future_domain_current_reject", "none", True, label, usage)
        return _signal(0.0, 0.5, "none", "future_domain_false_current_accept", False, label, usage)
    if label == "near_ood_generalization_candidate":
        if candidate_result.get("quarantined") or candidate_result.get("candidate_buffered"):
            return _signal(0.5, 0.0, "near_ood_candidate_buffer", "none", True, label, usage)
        if accepted:
            return _signal(0.0, 0.2, "none", "near_ood_false_supported_accept", False, label, usage)
        return _signal(0.0, 0.0, "near_ood_neutral_reject", "none", True, label, usage)
    return _signal(0.0, 0.0, "review_only", "none", True, label, usage)


def _signal(pos: float, tox: float, reward_reason: str, toxicity_reason: str, match: bool, label: str, usage: str) -> BoundaryRewardSignal:
    return BoundaryRewardSignal(
        positive_reward=pos,
        toxicity=tox,
        neutral_signal=1.0 if pos == 0.0 and tox == 0.0 else 0.0,
        reward_reason=reward_reason,
        toxicity_reason=toxicity_reason,
        expected_action_match=match,
        boundary_label=label,
        training_usage=usage,
    )
