from __future__ import annotations

from typing import Dict

from jianmu.self_learning.datasets.boundary_labels import BoundaryLabel


def nutrient_policy_for_boundary(boundary_label: str) -> Dict:
    if boundary_label == BoundaryLabel.CURRENT_SUPPORTED.value:
        return {
            "accept_reward": 1.0,
            "reject_reward": 0.0,
            "false_accept_toxicity": 0.0,
            "false_reject_toxicity": 1.0,
            "quarantine_reward": 0.0,
            "future_buffer_reward": 0.0,
            "training_usage": "train_current",
        }
    if boundary_label == BoundaryLabel.HARD_OOD.value:
        return {
            "accept_reward": 0.0,
            "reject_reward": 1.0,
            "false_accept_toxicity": 2.0,
            "false_reject_toxicity": 0.0,
            "quarantine_reward": 0.0,
            "future_buffer_reward": 0.0,
            "training_usage": "train_reject_boundary",
        }
    if boundary_label == BoundaryLabel.TRUE_FALSE_ACCEPT_TRAP.value:
        return {
            "accept_reward": 0.0,
            "reject_reward": 1.0,
            "false_accept_toxicity": 2.5,
            "false_reject_toxicity": 0.0,
            "quarantine_reward": 0.0,
            "future_buffer_reward": 0.0,
            "training_usage": "train_reject_boundary",
        }
    if boundary_label == BoundaryLabel.FUTURE_DOMAIN_CANDIDATE.value:
        return {
            "accept_reward": 0.0,
            "reject_reward": 0.2,
            "false_accept_toxicity": 0.5,
            "false_reject_toxicity": 0.0,
            "quarantine_reward": 0.0,
            "future_buffer_reward": 1.0,
            "training_usage": "future_buffer_only",
        }
    if boundary_label == BoundaryLabel.NEAR_OOD_GENERALIZATION_CANDIDATE.value:
        return {
            "accept_reward": 0.0,
            "reject_reward": 0.0,
            "false_accept_toxicity": 0.2,
            "false_reject_toxicity": 0.0,
            "quarantine_reward": 0.5,
            "future_buffer_reward": 1.0,
            "training_usage": "audit_only",
        }
    return {
        "accept_reward": 0.0,
        "reject_reward": 0.0,
        "false_accept_toxicity": 0.0,
        "false_reject_toxicity": 0.0,
        "quarantine_reward": 0.0,
        "future_buffer_reward": 0.0,
        "training_usage": "review_only",
    }


def attach_nutrient_policy(sample: Dict) -> Dict:
    policy = nutrient_policy_for_boundary(sample["boundary_label"])
    row = dict(sample)
    row.update(policy)
    return row


def boundary_reward_policy_valid(sample: Dict) -> bool:
    label = sample.get("boundary_label")
    if label == BoundaryLabel.CURRENT_SUPPORTED.value:
        return sample.get("accept_reward", 0) > 0 and sample.get("training_usage") == "train_current"
    if label in {BoundaryLabel.HARD_OOD.value, BoundaryLabel.TRUE_FALSE_ACCEPT_TRAP.value}:
        return sample.get("false_accept_toxicity", 0) > 0 and sample.get("training_usage") == "train_reject_boundary"
    if label == BoundaryLabel.FUTURE_DOMAIN_CANDIDATE.value:
        return sample.get("training_usage") == "future_buffer_only"
    if label == BoundaryLabel.NEAR_OOD_GENERALIZATION_CANDIDATE.value:
        return sample.get("training_usage") == "audit_only"
    if label == BoundaryLabel.LABEL_REVIEW_CANDIDATE.value:
        return sample.get("training_usage") == "review_only"
    return False
