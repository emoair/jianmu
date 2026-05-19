from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class LayerFreezeState:
    layer_name: str
    frozen: bool = False
    frozen_generation: Optional[int] = None
    accuracy_history: List[float] = field(default_factory=list)
    missing_rate_history: List[float] = field(default_factory=list)
    confidence_margin_history: List[float] = field(default_factory=list)
    unfreeze_count: int = 0
    reason: Optional[str] = None
    temporary_unfreeze_until: Optional[int] = None

    def to_dict(self) -> Dict:
        return {
            "layer_name": self.layer_name,
            "frozen": self.frozen,
            "frozen_generation": self.frozen_generation,
            "accuracy_history": self.accuracy_history,
            "missing_rate_history": self.missing_rate_history,
            "confidence_margin_history": self.confidence_margin_history,
            "unfreeze_count": self.unfreeze_count,
            "reason": self.reason,
            "temporary_unfreeze_until": self.temporary_unfreeze_until,
        }


@dataclass
class FreezeCriteria:
    accuracy_threshold: float = 0.90
    stability_window: int = 3
    max_missing_rate: float = 0.05
    min_confidence_margin: Optional[float] = None


def should_freeze(state: LayerFreezeState, criteria: FreezeCriteria) -> bool:
    window = criteria.stability_window
    if state.frozen:
        return False
    if len(state.accuracy_history) < window or len(state.missing_rate_history) < window:
        return False
    recent_acc = state.accuracy_history[-window:]
    recent_missing = state.missing_rate_history[-window:]
    if any(value < criteria.accuracy_threshold for value in recent_acc):
        return False
    if any(value > criteria.max_missing_rate for value in recent_missing):
        return False
    if criteria.min_confidence_margin is not None:
        if len(state.confidence_margin_history) < window:
            return False
        recent_margin = state.confidence_margin_history[-window:]
        if any(value < criteria.min_confidence_margin for value in recent_margin):
            return False
    return True


def should_unfreeze(state: LayerFreezeState, hard_case_attribution: Dict, threshold: float = 0.5) -> bool:
    if not state.frozen:
        return False
    layer = hard_case_attribution.get(state.layer_name, {})
    return float(layer.get("error_rate", 0.0)) > threshold or float(layer.get("severity", 0.0)) > threshold

