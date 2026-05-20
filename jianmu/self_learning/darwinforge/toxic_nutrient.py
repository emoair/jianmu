from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class NutrientSignal:
    positive_nutrient: float
    toxic_nutrient: float
    nutrient_type: str
    toxicity_reason: Optional[str]
    total_nutrient: float

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def compute_nutrient_signal(candidate: Dict, sample: Dict) -> NutrientSignal:
    supported = bool(sample.get("supported"))
    unsupported_pred = bool(candidate.get("unsupported_pred"))
    target_exact = bool(candidate.get("target_ir_exact_match"))
    expected_match = bool(candidate.get("expected_output_match"))
    high_conf_wrong = bool(candidate.get("rank", 99) == 1 and supported and not target_exact)
    if not supported and not unsupported_pred:
        toxic = 5.0
        return NutrientSignal(0.0, toxic, "toxic", "ood_false_accept", -toxic)
    if not supported and unsupported_pred:
        return NutrientSignal(2.0, 0.0, "positive", None, 2.0)
    if supported and target_exact:
        positive = 4.0 + (2.0 if expected_match else 0.0)
        return NutrientSignal(positive, 0.0, "positive", None, positive)
    if high_conf_wrong:
        toxic = 3.0
        return NutrientSignal(0.0, toxic, "toxic", "high_confidence_wrong_targetir", -toxic)
    return NutrientSignal(0.0, 0.0, "starvation", None, 0.0)
