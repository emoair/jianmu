from __future__ import annotations

from typing import Any, Dict


SUPPORTED = "current_supported_arithmetic"


def label_metadata(category: str) -> Dict[str, Any]:
    if category == SUPPORTED:
        return {
            "boundary_label": "current_supported",
            "expected_action": "accept_supported",
            "expected_type": "int",
            "nutrient_policy": {"positive": ["correct_accept"]},
            "toxicity_policy": {"toxic": ["false_reject"]},
        }
    if category == "future_domain_candidate":
        return {
            "boundary_label": "future_domain_candidate",
            "expected_action": "isolate_future",
            "expected_type": "unsupported",
            "nutrient_policy": {"positive": ["correct_future_isolation"]},
            "toxicity_policy": {"toxic": ["false_supported_accept"]},
        }
    if category == "near_ood_arithmetic":
        return {
            "boundary_label": "near_ood_arithmetic",
            "expected_action": "quarantine",
            "expected_type": "unsupported",
            "nutrient_policy": {"positive": ["correct_quarantine"]},
            "toxicity_policy": {"toxic": ["false_supported_accept"]},
        }
    if category == "label_review_candidate":
        return {
            "boundary_label": "label_review_candidate",
            "expected_action": "review",
            "expected_type": "review",
            "nutrient_policy": {"positive": []},
            "toxicity_policy": {"toxic": []},
        }
    return {
        "boundary_label": category,
        "expected_action": "reject",
        "expected_type": "unsupported",
        "nutrient_policy": {"positive": ["correct_reject"]},
        "toxicity_policy": {"toxic": ["false_accept_toxic"]},
    }
