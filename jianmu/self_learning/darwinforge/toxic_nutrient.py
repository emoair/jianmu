from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class NutrientSignal:
    positive_nutrient: float
    toxic_nutrient: float
    nutrient_type: str
    toxicity_reason: Optional[str]
    positive_reason: Optional[str]
    total_nutrient: float

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def compute_nutrient_signal(candidate: Dict, sample: Dict, prediction: Optional[Dict] = None) -> NutrientSignal:
    """Compute Toxic Nutrient（毒性养分） without using it as generation feature."""

    prediction = prediction or {}
    supported = bool(sample.get("supported"))
    unsupported_pred = bool(_first_present(candidate, prediction, "unsupported_pred", default=False))
    target_pred = _first_present(candidate, prediction, "target_ir_pred", "target_ir_canonical", default=None)
    target_exact = bool(_first_present(candidate, prediction, "target_ir_exact_match", default=False))
    expected_match = bool(_first_present(candidate, prediction, "expected_output_match", default=False))
    false_reject = bool(candidate.get("rejected") or prediction.get("rejected"))
    high_confidence = float(candidate.get("confidence", candidate.get("total_fitness", 0.0)) or 0.0) >= 1.0 or int(candidate.get("rank", 99)) == 1

    positive = 0.0
    toxic = 0.0
    positive_reason = "none"
    toxicity_reason = "none"

    if supported:
        if target_exact:
            positive += 4.0
            positive_reason = "target_ir_exact_match"
        if expected_match:
            positive += 2.0
            positive_reason = "expected_output_match" if positive_reason == "none" else positive_reason
        if false_reject:
            toxic += 4.0
            toxicity_reason = "high_confidence_wrong_supported"
        elif high_confidence and not target_exact and target_pred:
            toxic += 3.0
            toxicity_reason = "high_confidence_wrong_targetir"
    else:
        false_accept = not unsupported_pred and not bool(candidate.get("rejected") or prediction.get("rejected"))
        if false_accept:
            reason = _unsupported_false_accept_reason(sample)
            toxic += 7.0 if target_pred else 5.0
            toxicity_reason = reason
        else:
            positive += 2.0
            positive_reason = "correct_ood_rejection" if _is_ood(sample) else "correct_unsupported_rejection"

    if positive > 0 and toxic > 0:
        nutrient_type = "mixed"
    elif toxic > 0:
        nutrient_type = "toxic"
    elif positive > 0:
        nutrient_type = "positive"
    else:
        nutrient_type = "neutral"
    return NutrientSignal(positive, toxic, nutrient_type, toxicity_reason, positive_reason, positive - toxic)


def _first_present(*dicts_and_keys, default=None):
    dicts = [item for item in dicts_and_keys if isinstance(item, dict)]
    keys = [item for item in dicts_and_keys if isinstance(item, str)]
    for data in dicts:
        for key in keys:
            if key in data:
                return data[key]
    return default


def _unsupported_false_accept_reason(sample: Dict) -> str:
    if sample.get("input_mode") == "unsupported_arithmetic" or sample.get("unsupported_reason") in {"non_exact_division", "division_by_zero", "unsupported_depth"}:
        return "unsupported_arithmetic_false_accept"
    return "ood_false_accept"


def _is_ood(sample: Dict) -> bool:
    return sample.get("curriculum_stage") == "ood" or str(sample.get("input_mode", "")).startswith("ood_")
