from __future__ import annotations

from typing import Dict


def redqueen_v2_reward(components: Dict[str, float]) -> float:
    return round(
        components.get("top1_gain", 0.0)
        + 1.5 * components.get("candidate_miss_reduction", 0.0)
        + 0.8 * components.get("correct_output_in_beam_gain", 0.0)
        + 0.5 * components.get("contrastive_coverage_gain", 0.0)
        - components.get("duplicate_penalty", 0.0)
        - components.get("template_overfit_penalty", 0.0)
        - 1.5 * components.get("resource_cost_penalty", 0.0)
        - 2.0 * components.get("regression_dashboard_penalty", 0.0)
        - 3.0 * components.get("data_contract_violation_penalty", 0.0),
        6,
    )


def reward_component_schema() -> Dict[str, str]:
    return {
        "top1_gain": "offline evaluation estimate",
        "candidate_miss_reduction": "offline evaluation estimate",
        "correct_output_in_beam_gain": "offline evaluation estimate",
        "contrastive_coverage_gain": "contrastive audit metric",
        "duplicate_penalty": "dataset audit penalty",
        "template_overfit_penalty": "template audit penalty",
        "resource_cost_penalty": "recorded cost penalty",
        "regression_dashboard_penalty": "offline dashboard penalty",
        "data_contract_violation_penalty": "schema/audit/records penalty, not a runtime intercept",
    }
