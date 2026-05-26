from __future__ import annotations

from typing import Any, Dict


SUPPORTED = "current_supported_turing_substrate"


def label_metadata(category: str) -> Dict[str, Any]:
    if category == SUPPORTED:
        return {
            "expected_type": "int_stdout",
            "boundary_label": "current_supported",
            "expected_action": "accept_supported",
            "nutrient_policy": {"supported_correct": 1.0},
            "toxicity_policy": {"false_accept_toxic": 0.0},
        }
    if category == "future_domain_candidate":
        action = "isolate_future"
        label = "future_domain"
    elif category == "near_ood_program":
        action = "quarantine"
        label = "near_ood"
    elif category == "label_review_candidate":
        action = "review"
        label = "review"
    else:
        action = "reject"
        label = "unsupported_or_ood"
    return {
        "expected_type": "review" if category == "label_review_candidate" else "unsupported",
        "boundary_label": label,
        "expected_action": action,
        "nutrient_policy": {"supported_correct": 0.0},
        "toxicity_policy": {"false_accept_toxic": 1.0 if category == "true_false_accept_trap" else 0.5},
    }


def is_supported_category(category: str) -> bool:
    return category == SUPPORTED
