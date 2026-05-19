from dataclasses import dataclass, field
from typing import Dict, List, Optional

from jianmu.self_learning.branchchain.branch_chain import LAYER_DEFINITIONS
from jianmu.self_learning.darwinforge.freezing import FreezeCriteria


@dataclass
class LayerThresholdState:
    layer_name: str
    current_threshold: float
    start_threshold: float
    floor_threshold: float
    threshold_history: List[Dict] = field(default_factory=list)
    plateau_counter: int = 0
    blocked: bool = False
    frozen_threshold: Optional[float] = None
    last_best_accuracy: float = 0.0
    last_best_recall_at_k: float = 0.0

    def record_generation(self, accuracy: float, recall_at_k: float, missing_rate: float, correct_count: int, total_count: int):
        improved = accuracy > self.last_best_accuracy + 1e-9 or recall_at_k > self.last_best_recall_at_k + 1e-9
        if improved:
            self.plateau_counter = 0
            self.last_best_accuracy = max(self.last_best_accuracy, accuracy)
            self.last_best_recall_at_k = max(self.last_best_recall_at_k, recall_at_k)
        else:
            self.plateau_counter += 1
        self.threshold_history.append({
            "threshold": round(self.current_threshold, 4),
            "accuracy": accuracy,
            "recall_at_k": recall_at_k,
            "missing_rate": missing_rate,
            "correct_count": correct_count,
            "total_count": total_count,
        })

    def should_anneal(self, criteria: FreezeCriteria) -> bool:
        if self.blocked or self.frozen_threshold is not None:
            return False
        if self.plateau_counter < criteria.plateau_patience:
            return False
        if not self.threshold_history:
            return False
        recent = self.threshold_history[-1]
        return recent["missing_rate"] <= criteria.max_missing_rate

    def anneal(self, criteria: FreezeCriteria):
        if self.current_threshold <= self.floor_threshold + 1e-9:
            self.mark_blocked()
            return
        self.current_threshold = round(max(self.floor_threshold, self.current_threshold - criteria.anneal_step), 4)
        self.plateau_counter = 0

    def mark_frozen(self):
        self.frozen_threshold = self.current_threshold

    def mark_blocked(self):
        self.blocked = True

    def to_dict(self):
        return {
            "layer_name": self.layer_name,
            "current_threshold": self.current_threshold,
            "start_threshold": self.start_threshold,
            "floor_threshold": self.floor_threshold,
            "threshold_history": self.threshold_history,
            "plateau_counter": self.plateau_counter,
            "blocked": self.blocked,
            "frozen_threshold": self.frozen_threshold,
            "last_best_accuracy": self.last_best_accuracy,
            "last_best_recall_at_k": self.last_best_recall_at_k,
        }


class ThresholdSearchController:
    def __init__(self, criteria: FreezeCriteria):
        self.criteria = criteria
        self.states = {
            layer: LayerThresholdState(
                layer_name=layer,
                current_threshold=criteria.get_start_threshold(layer),
                start_threshold=criteria.get_start_threshold(layer),
                floor_threshold=criteria.get_floor_threshold(layer),
            )
            for layer, _ in LAYER_DEFINITIONS
        }
        self.anneal_events: List[Dict] = []
        self.block_events: List[Dict] = []

    def current_threshold(self, layer_name: str) -> float:
        return self.states[layer_name].current_threshold

    def update(self, layer_name: str, metrics: Dict):
        self.states[layer_name].record_generation(
            accuracy=float(metrics.get("accuracy", 0.0)),
            recall_at_k=float(metrics.get("recall_at_k", 0.0)),
            missing_rate=float(metrics.get("missing_rate", 1.0)),
            correct_count=int(metrics.get("correct_count", 0)),
            total_count=int(metrics.get("total_count", 0)),
        )

    def maybe_anneal(self, layer_name: str, generation: int = 0):
        state = self.states[layer_name]
        if state.should_anneal(self.criteria):
            old = state.current_threshold
            state.anneal(self.criteria)
            event = {"generation": generation, "layer": layer_name, "from": old, "to": state.current_threshold}
            self.anneal_events.append(event)
            if state.blocked:
                self.block_events.append({"generation": generation, "layer": layer_name, "floor": state.floor_threshold})
            return event
        return None

    def mark_frozen(self, layer_name: str):
        self.states[layer_name].mark_frozen()

    def mark_blocked(self, layer_name: str):
        self.states[layer_name].mark_blocked()

    def to_dict(self):
        return {
            "states": {layer: state.to_dict() for layer, state in self.states.items()},
            "anneal_events": self.anneal_events,
            "block_events": self.block_events,
        }
