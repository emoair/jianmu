import math
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
    current_threshold: Optional[float] = None
    frozen_threshold: Optional[float] = None
    blocked: bool = False

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
            "current_threshold": self.current_threshold,
            "frozen_threshold": self.frozen_threshold,
            "blocked": self.blocked,
        }


@dataclass
class FreezeCriteria:
    accuracy_threshold: float = 0.90
    stability_window: int = 3
    max_missing_rate: float = 0.05
    min_confidence_margin: Optional[float] = None
    high_start_threshold: float = 0.98
    global_floor_threshold: float = 0.80
    plateau_patience: int = 6
    anneal_step: float = 0.025
    use_integer_correct_count: bool = True
    layer_start_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "task_scope": 0.98,
        "language_target": 0.98,
        "semantic_domain": 0.95,
        "support_gate": 0.95,
        "arithmetic_family": 0.95,
        "structure_policy": 0.95,
        "slot_binding_policy": 0.95,
        "target_builder": 0.95,
    })
    layer_floor_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "task_scope": 0.90,
        "language_target": 0.90,
        "semantic_domain": 0.85,
        "support_gate": 0.85,
        "arithmetic_family": 0.80,
        "structure_policy": 0.80,
        "slot_binding_policy": 0.75,
        "target_builder": 0.80,
    })

    def get_start_threshold(self, layer_name: str) -> float:
        return self.layer_start_thresholds.get(layer_name, self.high_start_threshold)

    def get_floor_threshold(self, layer_name: str) -> float:
        return self.layer_floor_thresholds.get(layer_name, self.global_floor_threshold)


def should_freeze(state: LayerFreezeState, criteria: FreezeCriteria) -> bool:
    window = criteria.stability_window
    if state.frozen:
        return False
    if len(state.accuracy_history) < window or len(state.missing_rate_history) < window:
        return False
    recent_acc = state.accuracy_history[-window:]
    recent_missing = state.missing_rate_history[-window:]
    threshold = state.current_threshold if state.current_threshold is not None else criteria.accuracy_threshold
    if any(value < threshold for value in recent_acc):
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


def get_start_threshold(criteria: FreezeCriteria, layer_name: str) -> float:
    return criteria.get_start_threshold(layer_name)


def get_floor_threshold(criteria: FreezeCriteria, layer_name: str) -> float:
    return criteria.get_floor_threshold(layer_name)


def required_correct_count(dataset_size: int, threshold: float) -> int:
    return int(math.ceil(dataset_size * threshold - 1e-9))


def passes_threshold(correct_count: int, total_count: int, threshold: float, use_integer_correct_count: bool = True) -> bool:
    if total_count <= 0:
        return False
    if use_integer_correct_count:
        return correct_count >= required_correct_count(total_count, threshold)
    return (correct_count / total_count) >= threshold


def should_unfreeze(state: LayerFreezeState, hard_case_attribution: Dict, threshold: float = 0.5) -> bool:
    if not state.frozen:
        return False
    layer = hard_case_attribution.get(state.layer_name, {})
    return float(layer.get("error_rate", 0.0)) > threshold or float(layer.get("severity", 0.0)) > threshold
