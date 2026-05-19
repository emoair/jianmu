from dataclasses import dataclass, field
from typing import Dict, List

from jianmu.self_learning.branchchain.branch_chain import LAYER_DEFINITIONS
from jianmu.self_learning.darwinforge.freezing import FreezeCriteria, LayerFreezeState, passes_threshold, should_freeze, should_unfreeze
from jianmu.self_learning.darwinforge.threshold_search import ThresholdSearchController


DEFAULT_LAYER_ORDER = [layer for layer, _ in LAYER_DEFINITIONS]


@dataclass
class CurriculumPlan:
    layer_order: List[str] = field(default_factory=lambda: list(DEFAULT_LAYER_ORDER))
    active_layer_index: int = 0
    freeze_states: Dict[str, LayerFreezeState] = field(default_factory=dict)
    criteria: FreezeCriteria = field(default_factory=FreezeCriteria)
    unfreeze_generations: int = 3
    freeze_events: List[Dict] = field(default_factory=list)
    unfreeze_events: List[Dict] = field(default_factory=list)
    threshold_anneal_events: List[Dict] = field(default_factory=list)
    threshold_block_events: List[Dict] = field(default_factory=list)
    blocked_layers: List[str] = field(default_factory=list)
    allow_advance_on_block: bool = False
    generation: int = 0
    threshold_controller: ThresholdSearchController = None

    def __post_init__(self):
        if self.threshold_controller is None:
            self.threshold_controller = ThresholdSearchController(self.criteria)
        for layer in self.layer_order:
            self.freeze_states.setdefault(layer, LayerFreezeState(layer_name=layer))
            self.freeze_states[layer].current_threshold = self.threshold_controller.current_threshold(layer)

    def active_layer(self) -> str:
        return self.layer_order[min(self.active_layer_index, len(self.layer_order) - 1)]

    def is_frozen(self, layer_name: str) -> bool:
        state = self.freeze_states[layer_name]
        if state.temporary_unfreeze_until is not None and self.generation <= state.temporary_unfreeze_until:
            return False
        return state.frozen

    def can_mutate(self, layer_name: str) -> bool:
        if self.is_frozen(layer_name):
            return False
        if layer_name == self.active_layer():
            return True
        state = self.freeze_states[layer_name]
        return state.temporary_unfreeze_until is not None and self.generation <= state.temporary_unfreeze_until

    def update_layer_metrics(self, layer_name: str, accuracy: float, missing_rate: float, confidence_margin: float = 0.0):
        state = self.freeze_states[layer_name]
        state.accuracy_history.append(float(accuracy))
        state.missing_rate_history.append(float(missing_rate))
        state.confidence_margin_history.append(float(confidence_margin))

    def maybe_freeze_active_layer(self):
        layer = self.active_layer()
        state = self.freeze_states[layer]
        state.current_threshold = self.threshold_controller.current_threshold(layer)
        if should_freeze(state, self.criteria):
            state.frozen = True
            state.frozen_generation = self.generation
            state.frozen_threshold = state.current_threshold
            state.reason = "freeze_criteria_met"
            self.threshold_controller.mark_frozen(layer)
            self.freeze_events.append({
                "generation": self.generation,
                "layer": layer,
                "reason": state.reason,
                "frozen_threshold": state.frozen_threshold,
            })
            return True
        event = self.threshold_controller.maybe_anneal(layer, generation=self.generation)
        if event:
            self.threshold_anneal_events.append(event)
            state.current_threshold = self.threshold_controller.current_threshold(layer)
        if self.threshold_controller.states[layer].blocked:
            state.blocked = True
            if layer not in self.blocked_layers:
                self.blocked_layers.append(layer)
                block_event = {"generation": self.generation, "layer": layer, "reason": "below_floor"}
                self.threshold_block_events.append(block_event)
        return False

    def maybe_advance(self):
        current = self.active_layer()
        if (
            (self.freeze_states[current].frozen or (self.allow_advance_on_block and current in self.blocked_layers))
            and self.active_layer_index < len(self.layer_order) - 1
        ):
            self.active_layer_index += 1
            return True
        return False

    def maybe_unfreeze_from_hard_cases(self, attribution: Dict, threshold: float = 0.5):
        events = []
        for layer_name, state in self.freeze_states.items():
            if should_unfreeze(state, attribution, threshold):
                state.frozen = False
                state.temporary_unfreeze_until = self.generation + self.unfreeze_generations
                state.unfreeze_count += 1
                state.reason = "hard_case_conditional_unfreeze"
                event = {"generation": self.generation, "layer": layer_name, "reason": state.reason}
                self.unfreeze_events.append(event)
                events.append(event)
        return events

    def tick(self, generation: int):
        self.generation = generation
        for state in self.freeze_states.values():
            if state.temporary_unfreeze_until is not None and generation > state.temporary_unfreeze_until:
                state.temporary_unfreeze_until = None

    def to_dict(self):
        return {
            "layer_order": self.layer_order,
            "active_layer_index": self.active_layer_index,
            "active_layer": self.active_layer(),
            "freeze_states": {k: v.to_dict() for k, v in self.freeze_states.items()},
            "criteria": self.criteria.__dict__,
            "unfreeze_generations": self.unfreeze_generations,
            "freeze_events": self.freeze_events,
            "unfreeze_events": self.unfreeze_events,
            "threshold_controller": self.threshold_controller.to_dict(),
            "threshold_anneal_events": self.threshold_anneal_events,
            "threshold_block_events": self.threshold_block_events,
            "blocked_layers": self.blocked_layers,
            "frozen_threshold_by_layer": {
                layer: state.frozen_threshold for layer, state in self.freeze_states.items() if state.frozen_threshold is not None
            },
            "generation": self.generation,
        }
