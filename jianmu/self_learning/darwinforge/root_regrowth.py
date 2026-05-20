from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class RegrowthEvent:
    generation: int
    root_id: str
    sample_id: str
    stable_prefix: List[List[str]]
    regrowth_fork_point: Optional[str]
    reason: str
    created_clone_layers: List[str]
    success: bool = False

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def find_stable_prefix(root, min_prefix_length: int = 1) -> List[List[str]]:
    if len(root.stable_prefix) >= min_prefix_length:
        return root.stable_prefix
    decisions = getattr(root.branch_path, "decisions", [])
    return [[decision.layer_name, decision.selected] for decision in decisions[:min_prefix_length]]


def choose_regrowth_fork_point(root, target_path: List = None) -> Optional[str]:
    if root.first_confidence_collapse_layer:
        decisions = getattr(root.branch_path, "decisions", [])
        previous = None
        for decision in decisions:
            if decision.layer_name == root.first_confidence_collapse_layer:
                return previous.layer_name if previous else decision.layer_name
            previous = decision
    if root.first_wrong_layer:
        decisions = getattr(root.branch_path, "decisions", [])
        previous = None
        for decision in decisions:
            if decision.layer_name == root.first_wrong_layer:
                return previous.layer_name if previous else decision.layer_name
            previous = decision
        return root.first_wrong_layer
    if root.stable_prefix:
        return root.stable_prefix[-1][0]
    return None


def plan_regrowth(root, generation: int, layer_order: List[str], window: int = 1, reason: str = "low_score_correct") -> RegrowthEvent:
    fork = choose_regrowth_fork_point(root)
    if fork in layer_order:
        index = layer_order.index(fork)
        clone_layers = layer_order[index + 1 : index + 1 + max(window, 1)]
    else:
        clone_layers = layer_order[: max(window, 1)]
    return RegrowthEvent(
        generation=generation,
        root_id=root.root_id,
        sample_id=root.sample_id,
        stable_prefix=find_stable_prefix(root),
        regrowth_fork_point=fork,
        reason=reason,
        created_clone_layers=clone_layers,
    )


def summarize_regrowth(events) -> Dict:
    return {
        "regrowth_event_count": len(events),
        "regrowth_success_count": sum(1 for event in events if event.success),
    }
