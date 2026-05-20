from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class NecrosisEvent:
    generation: int
    root_id: str
    sample_id: str
    reason: str
    action: str
    observed_count: int = 1

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


class NecrosisQueue:
    def __init__(self, no_nutrient_generations: int = 3):
        self.no_nutrient_generations = no_nutrient_generations
        self._counts: Dict[str, int] = {}
        self.events = []

    def observe(self, root, generation: int, phase: str = "early") -> NecrosisEvent:
        reason = _necrosis_reason(root)
        self._counts[root.root_id] = self._counts.get(root.root_id, 0) + 1
        count = self._counts[root.root_id]
        if phase == "late" and count >= self.no_nutrient_generations:
            action = "pruned"
        elif count >= self.no_nutrient_generations:
            action = "decayed"
        else:
            action = "queued"
        event = NecrosisEvent(generation, root.root_id, root.sample_id, reason, action, count)
        self.events.append(event)
        root.necrosis_state = action
        return event

    def summary(self) -> Dict:
        return summarize_necrosis(self.events)


def _necrosis_reason(root) -> str:
    if root.root_type == "high_score_wrong":
        return "high_score_wrong"
    if root.root_type == "lucky_correct_root":
        return "lucky_correct_reproduction_failed"
    if root.nutrient_score <= 0:
        return "no_nutrient"
    return "regrowth_replaced"


def summarize_necrosis(events) -> Dict:
    return {
        "necrosis_candidate_count": len(events),
        "necrosis_decay_count": sum(1 for event in events if event.action == "decayed"),
        "necrosis_pruned_count": sum(1 for event in events if event.action == "pruned"),
        "high_score_wrong_necrosis_count": sum(1 for event in events if event.reason == "high_score_wrong"),
        "lucky_correct_necrosis_count": sum(1 for event in events if event.reason == "lucky_correct_reproduction_failed"),
    }
