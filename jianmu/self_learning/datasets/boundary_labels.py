from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, List


class BoundaryLabel(str, Enum):
    CURRENT_SUPPORTED = "current_supported"
    HARD_OOD = "hard_ood"
    TRUE_FALSE_ACCEPT_TRAP = "true_false_accept_trap"
    FUTURE_DOMAIN_CANDIDATE = "future_domain_candidate"
    NEAR_OOD_GENERALIZATION_CANDIDATE = "near_ood_generalization_candidate"
    LABEL_REVIEW_CANDIDATE = "label_review_candidate"


class ExpectedAction(str, Enum):
    ACCEPT_AND_SYNTHESIZE = "accept_and_synthesize"
    REJECT = "reject"
    REJECT_BUT_KEEP_FUTURE_CANDIDATE = "reject_but_keep_future_candidate"
    QUARANTINE_FOR_REVIEW = "quarantine_for_review"
    CANDIDATE_BUFFER_ONLY = "candidate_buffer_only"


class NutrientPolicy(str, Enum):
    POSITIVE_ON_CORRECT_ACCEPT = "positive_on_correct_accept"
    POSITIVE_ON_CORRECT_REJECT = "positive_on_correct_reject"
    TOXIC_ON_FALSE_ACCEPT = "toxic_on_false_accept"
    TOXIC_ON_FALSE_REJECT = "toxic_on_false_reject"
    NEUTRAL_ON_CURRENT_REJECT = "neutral_on_current_reject"
    WEAK_POSITIVE_ON_CURRENT_REJECT = "weak_positive_on_current_reject"
    NO_TRAINING_SIGNAL_REVIEW_ONLY = "no_training_signal_review_only"


REQUIRED_BOUNDARY_SAMPLE_FIELDS = [
    "sample_id",
    "raw_text",
    "canonical_text",
    "input_mode",
    "boundary_label",
    "expected_action",
    "nutrient_policy",
    "toxicity_policy",
    "current_support_status",
    "future_support_status",
    "source_version",
    "source_reason",
]


def validate_boundary_sample(sample: Dict) -> List[str]:
    issues: List[str] = []
    for field in REQUIRED_BOUNDARY_SAMPLE_FIELDS:
        if field not in sample:
            issues.append(f"missing_required_field:{field}")
    label = sample.get("boundary_label")
    has_target = bool(sample.get("target_ir") or sample.get("expected_output"))
    if label == BoundaryLabel.CURRENT_SUPPORTED.value and not (sample.get("target_ir") and sample.get("expected_output")):
        issues.append("current_supported_missing_targetir_or_expected_output")
    if label != BoundaryLabel.CURRENT_SUPPORTED.value and has_target:
        issues.append("non_supported_has_targetir")
    if label == BoundaryLabel.FUTURE_DOMAIN_CANDIDATE.value and sample.get("training_usage") == "train_current":
        issues.append("future_domain_in_train_current")
    if label == BoundaryLabel.NEAR_OOD_GENERALIZATION_CANDIDATE.value and sample.get("training_usage") == "train_current":
        issues.append("near_ood_in_train_current")
    return issues


def boundary_label_values() -> List[str]:
    return [label.value for label in BoundaryLabel]


def make_boundary_sample(
    *,
    sample_id: str,
    raw_text: str,
    canonical_text: str,
    input_mode: str,
    boundary_label: BoundaryLabel | str,
    expected_action: ExpectedAction | str,
    nutrient_policy: Iterable[NutrientPolicy | str],
    toxicity_policy: Iterable[NutrientPolicy | str],
    current_support_status: str,
    future_support_status: str,
    source_version: str,
    source_reason: str,
    target_ir: str | None = None,
    expected_output: str | None = None,
    ood_class: str | None = None,
    paraphrase_group_id: str | None = None,
    target_group_id: str | None = None,
    training_usage: str | None = None,
) -> Dict:
    label_value = boundary_label.value if isinstance(boundary_label, BoundaryLabel) else str(boundary_label)
    row = {
        "sample_id": sample_id,
        "raw_text": raw_text,
        "canonical_text": canonical_text,
        "input_mode": input_mode,
        "boundary_label": label_value,
        "expected_action": expected_action.value if isinstance(expected_action, ExpectedAction) else str(expected_action),
        "nutrient_policy": [item.value if isinstance(item, NutrientPolicy) else str(item) for item in nutrient_policy],
        "toxicity_policy": [item.value if isinstance(item, NutrientPolicy) else str(item) for item in toxicity_policy],
        "current_support_status": current_support_status,
        "future_support_status": future_support_status,
        "source_version": source_version,
        "source_reason": source_reason,
        "ood_class": ood_class,
        "paraphrase_group_id": paraphrase_group_id or f"pg-{sample_id}",
        "target_group_id": target_group_id,
        "training_usage": training_usage,
    }
    if label_value == BoundaryLabel.CURRENT_SUPPORTED.value:
        row["target_ir"] = target_ir
        row["expected_output"] = expected_output
    return row
