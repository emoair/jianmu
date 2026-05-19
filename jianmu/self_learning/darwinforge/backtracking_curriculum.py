from dataclasses import dataclass, field
from typing import Dict, List, Optional

from jianmu.self_learning.branchchain.branch_chain import LAYER_DEFINITIONS


@dataclass
class PerfectLayerCriteria:
    require_perfect: bool = True
    perfect_accuracy: float = 1.0
    perfect_stability_window: int = 2
    patience_generations: int = 8
    backtrack_window: int = 1
    backtrack_generations: int = 5
    max_backtrack_attempts_per_layer: int = 3
    allow_highest_stable_fallback: bool = False
    fallback_threshold: float = 0.95
    upstream_mutation_scale: float = 0.3


@dataclass
class LayerTrainingState:
    layer_name: str
    status: str = "pending"
    accuracy_history: List[float] = field(default_factory=list)
    recall_at_k_history: List[float] = field(default_factory=list)
    missing_rate_history: List[float] = field(default_factory=list)
    correct_count_history: List[int] = field(default_factory=list)
    total_count_history: List[int] = field(default_factory=list)
    frozen_generation: Optional[int] = None
    perfect_generation: Optional[int] = None
    backtrack_count: int = 0
    last_improvement_generation: int = 0
    blocked_reason: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "layer_name": self.layer_name,
            "status": self.status,
            "accuracy_history": list(self.accuracy_history),
            "recall_at_k_history": list(self.recall_at_k_history),
            "missing_rate_history": list(self.missing_rate_history),
            "correct_count_history": list(self.correct_count_history),
            "total_count_history": list(self.total_count_history),
            "frozen_generation": self.frozen_generation,
            "perfect_generation": self.perfect_generation,
            "backtrack_count": self.backtrack_count,
            "last_improvement_generation": self.last_improvement_generation,
            "blocked_reason": self.blocked_reason,
        }


@dataclass
class BacktrackingEvent:
    generation: int
    active_layer: str
    unfrozen_layers: List[str]
    reason: str
    before_accuracy: float
    after_accuracy: Optional[float] = None
    outcome: str = "no_improvement"

    def to_dict(self) -> Dict:
        return {
            "generation": self.generation,
            "active_layer": self.active_layer,
            "unfrozen_layers": list(self.unfrozen_layers),
            "reason": self.reason,
            "before_accuracy": self.before_accuracy,
            "after_accuracy": self.after_accuracy,
            "outcome": self.outcome,
        }


class PerfectLayerCurriculumPlan:
    def __init__(self, layer_order: List[str] = None, criteria: PerfectLayerCriteria = None):
        self.layer_order = layer_order or [name for name, _ in LAYER_DEFINITIONS]
        self.criteria = criteria or PerfectLayerCriteria()
        self.active_layer_index = 0
        self.states = {layer: LayerTrainingState(layer) for layer in self.layer_order}
        if self.layer_order:
            self.states[self.layer_order[0]].status = "active"
        self.backtracking_events: List[BacktrackingEvent] = []
        self.freeze_events: List[Dict] = []
        self.blocked_layers: List[str] = []
        self.backtracking_until: Dict[str, int] = {}
        self.current_generation = 0

    def active_layer(self) -> str:
        if self.active_layer_index >= len(self.layer_order):
            return self.layer_order[-1]
        return self.layer_order[self.active_layer_index]

    def is_frozen(self, layer_name: str) -> bool:
        return self.states[layer_name].status == "frozen"

    def can_mutate(self, layer_name: str) -> bool:
        return self.states[layer_name].status in {"active", "backtracking"}

    def mutation_scale(self, layer_name: str) -> float:
        if self.states[layer_name].status == "backtracking" and layer_name != self.active_layer():
            return self.criteria.upstream_mutation_scale
        return 1.0 if self.can_mutate(layer_name) else 0.0

    def trainable_layers(self) -> List[str]:
        return [layer for layer in self.layer_order if self.can_mutate(layer)]

    def update_layer_metrics(self, layer_name: str, accuracy: float, recall_at_k: float, missing_rate: float, correct_count: int, total_count: int, generation: int):
        self.current_generation = generation
        state = self.states[layer_name]
        previous_best = max(state.accuracy_history, default=-1.0)
        state.accuracy_history.append(accuracy)
        state.recall_at_k_history.append(recall_at_k)
        state.missing_rate_history.append(missing_rate)
        state.correct_count_history.append(correct_count)
        state.total_count_history.append(total_count)
        if accuracy > previous_best:
            state.last_improvement_generation = generation

    def should_freeze_layer(self, layer_name: str) -> bool:
        state = self.states[layer_name]
        window = self.criteria.perfect_stability_window
        if len(state.accuracy_history) < window:
            return False
        recent_accuracy = state.accuracy_history[-window:]
        recent_missing = state.missing_rate_history[-window:]
        recent_correct = state.correct_count_history[-window:]
        recent_total = state.total_count_history[-window:]
        if self.criteria.require_perfect:
            return all(
                accuracy >= self.criteria.perfect_accuracy
                and missing == 0
                and total > 0
                and correct == total
                for accuracy, missing, correct, total in zip(recent_accuracy, recent_missing, recent_correct, recent_total)
            )
        threshold = self.criteria.fallback_threshold if self.criteria.allow_highest_stable_fallback else self.criteria.perfect_accuracy
        return all(accuracy >= threshold and missing == 0 for accuracy, missing in zip(recent_accuracy, recent_missing))

    def freeze_layer(self, layer_name: str, generation: int):
        state = self.states[layer_name]
        state.status = "frozen"
        state.frozen_generation = generation
        state.perfect_generation = generation
        event = {
            "generation": generation,
            "layer": layer_name,
            "required_correct": state.total_count_history[-1] if state.total_count_history else 0,
            "actual_correct": state.correct_count_history[-1] if state.correct_count_history else 0,
            "frozen_at_accuracy": state.accuracy_history[-1] if state.accuracy_history else 0.0,
            "reason": "perfect_layer_criteria_met",
        }
        self.freeze_events.append(event)

    def should_backtrack(self, layer_name: str, generation: int) -> bool:
        state = self.states[layer_name]
        if state.status != "active":
            return False
        if self.should_freeze_layer(layer_name):
            return False
        if state.backtrack_count >= self.criteria.max_backtrack_attempts_per_layer:
            return False
        return generation - state.last_improvement_generation >= self.criteria.patience_generations

    def start_backtracking(self, layer_name: str, generation: int) -> BacktrackingEvent:
        index = self.layer_order.index(layer_name)
        start = max(0, index - self.criteria.backtrack_window)
        window = self.layer_order[start:index + 1]
        before_accuracy = self.states[layer_name].accuracy_history[-1] if self.states[layer_name].accuracy_history else 0.0
        for layer in window:
            self.states[layer].status = "backtracking"
            self.backtracking_until[layer] = generation + self.criteria.backtrack_generations
        self.states[layer_name].backtrack_count += 1
        event = BacktrackingEvent(
            generation=generation,
            active_layer=layer_name,
            unfrozen_layers=window,
            reason="active_layer_stalled_before_perfect",
            before_accuracy=before_accuracy,
            outcome="no_improvement",
        )
        self.backtracking_events.append(event)
        return event

    def finish_backtracking(self, layer_name: str, generation: int, improved: bool):
        state = self.states[layer_name]
        after_accuracy = state.accuracy_history[-1] if state.accuracy_history else 0.0
        for event in reversed(self.backtracking_events):
            if event.active_layer == layer_name and event.after_accuracy is None:
                event.after_accuracy = after_accuracy
                event.outcome = "improved" if improved else "no_improvement"
                break
        for layer, until in list(self.backtracking_until.items()):
            if generation >= until:
                if self.states[layer].status == "backtracking":
                    self.states[layer].status = "active" if layer == layer_name else "frozen"
                self.backtracking_until.pop(layer, None)
        if not improved and state.backtrack_count >= self.criteria.max_backtrack_attempts_per_layer:
            state.status = "blocked"
            state.blocked_reason = "max_backtrack_attempts_exceeded"
            if layer_name not in self.blocked_layers:
                self.blocked_layers.append(layer_name)
            for event in reversed(self.backtracking_events):
                if event.active_layer == layer_name:
                    event.outcome = "blocked"
                    break

    def maybe_advance(self, generation: int):
        active = self.active_layer()
        if self.states[active].status == "blocked":
            return
        if self.states[active].status != "frozen":
            return
        if self.active_layer_index + 1 < len(self.layer_order):
            self.active_layer_index += 1
            next_layer = self.active_layer()
            if self.states[next_layer].status == "pending":
                self.states[next_layer].status = "active"

    def step(self, generation: int):
        active = self.active_layer()
        state = self.states[active]
        if self.should_freeze_layer(active):
            self.freeze_layer(active, generation)
            for event in reversed(self.backtracking_events):
                if event.active_layer == active and event.after_accuracy is None:
                    event.after_accuracy = state.accuracy_history[-1]
                    event.outcome = "frozen_after_backtrack"
                    break
            self.maybe_advance(generation)
            return
        if state.status == "backtracking":
            before = None
            for event in reversed(self.backtracking_events):
                if event.active_layer == active and event.after_accuracy is None:
                    before = event.before_accuracy
                    break
            improved = before is not None and state.accuracy_history and state.accuracy_history[-1] > before
            self.finish_backtracking(active, generation, improved)
            return
        if self.should_backtrack(active, generation):
            self.start_backtracking(active, generation)
            return

    def to_dict(self) -> Dict:
        return {
            "layer_order": list(self.layer_order),
            "active_layer_index": self.active_layer_index,
            "active_layer": self.active_layer(),
            "trainable_layers": self.trainable_layers(),
            "states": {layer: state.to_dict() for layer, state in self.states.items()},
            "criteria": self.criteria.__dict__,
            "backtracking_events": [event.to_dict() for event in self.backtracking_events],
            "freeze_events": list(self.freeze_events),
            "blocked_layers": list(self.blocked_layers),
        }
