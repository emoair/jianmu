from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional


@dataclass
class RootLifecycleState:
    root_id: str
    sample_id: str
    path_signature: str
    state: str = "active"
    nutrient_history: List[float] = field(default_factory=list)
    starvation_counter: int = 0
    ttl: int = 8
    generation_created: int = 0
    generation_last_nourished: Optional[int] = None
    archived_reason: Optional[str] = None
    parent_root_id: Optional[str] = None
    replacement_root_ids: List[str] = field(default_factory=list)
    frozen_weights_snapshot: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


@dataclass
class RootLifecycleConfig:
    starvation_patience: int = 3
    max_ttl: int = 8
    necrosis_threshold: int = 4
    replacement_budget_per_generation: int = 32
    max_active_roots: int = 256
    max_archive_size: int = 4096


def update_root_lifecycle(
    root_states: Dict[str, RootLifecycleState],
    current_candidates: Iterable[Dict],
    nutrient_signals: Dict[str, float],
    config: RootLifecycleConfig = None,
    generation: int = 0,
) -> Dict:
    config = config or RootLifecycleConfig()
    events = []
    replacement_count = 0
    resource_released = 0
    for candidate in current_candidates:
        root_id = candidate["root_id"]
        state = root_states.setdefault(
            root_id,
            RootLifecycleState(
                root_id=root_id,
                sample_id=candidate.get("sample_id", ""),
                path_signature=candidate.get("path_signature", root_id),
                ttl=config.max_ttl,
                generation_created=generation,
                parent_root_id=candidate.get("parent_root_id"),
            ),
        )
        nutrient = float(nutrient_signals.get(root_id, candidate.get("nutrient_score", 0.0)))
        state.nutrient_history.append(nutrient)
        if nutrient > 0:
            state.starvation_counter = 0
            state.ttl = min(config.max_ttl, state.ttl + 1)
            state.generation_last_nourished = generation
            state.state = "stable" if len([n for n in state.nutrient_history[-3:] if n > 0]) >= 3 else "nourished"
            events.append({"root_id": root_id, "event": "nourished", "generation": generation})
        else:
            state.starvation_counter += 1
            state.ttl -= 1
            state.state = "starving"
            events.append({"root_id": root_id, "event": "starving", "generation": generation})
        if candidate.get("root_type") == "high_score_wrong":
            state.starvation_counter += 2
            state.state = "necrosis_candidate"
            events.append({"root_id": root_id, "event": "necrosis_candidate", "generation": generation, "reason": "high_score_wrong"})
        if candidate.get("stable_prefix") and nutrient <= 0 and replacement_count < config.replacement_budget_per_generation:
            replacement_id = f"{root_id}:replacement:{generation}"
            state.replacement_root_ids.append(replacement_id)
            root_states[replacement_id] = RootLifecycleState(
                root_id=replacement_id,
                sample_id=state.sample_id,
                path_signature=">".join(f"{layer}={option}" for layer, option in candidate.get("stable_prefix", [])),
                state="replacement",
                ttl=config.max_ttl,
                generation_created=generation,
                parent_root_id=root_id,
            )
            replacement_count += 1
            events.append({"root_id": replacement_id, "parent_root_id": root_id, "event": "replacement_root", "generation": generation})
        if state.ttl <= 0 or state.starvation_counter >= config.necrosis_threshold:
            if state.state != "necrotic_archived":
                state.state = "necrotic_archived"
                state.archived_reason = "ttl_or_starvation"
                state.frozen_weights_snapshot = {"path_signature": state.path_signature}
                resource_released += 1
                events.append({"root_id": root_id, "event": "necrotic_archived", "generation": generation})
    _enforce_active_budget(root_states, config, events, generation)
    counts = _counts(root_states)
    return {
        **counts,
        "resource_released_count": resource_released,
        "archive_size": counts["necrotic_archived_count"],
        "events": events,
        "states": [state.to_dict() for state in root_states.values()],
    }


def _enforce_active_budget(root_states: Dict[str, RootLifecycleState], config: RootLifecycleConfig, events: List[Dict], generation: int) -> None:
    active = [state for state in root_states.values() if state.state in {"active", "nourished", "starving", "necrosis_candidate", "replacement"}]
    if len(active) <= config.max_active_roots:
        return
    overflow = sorted(active, key=lambda state: (state.starvation_counter, -state.ttl), reverse=True)[config.max_active_roots :]
    for state in overflow:
        state.state = "necrotic_archived"
        state.archived_reason = "resource_gate"
        events.append({"root_id": state.root_id, "event": "necrotic_archived", "generation": generation, "reason": "resource_gate"})


def _counts(root_states: Dict[str, RootLifecycleState]) -> Dict:
    states = list(root_states.values())
    return {
        "active_root_count": sum(1 for state in states if state.state == "active"),
        "nourished_root_count": sum(1 for state in states if state.state == "nourished"),
        "starving_root_count": sum(1 for state in states if state.state == "starving"),
        "necrosis_candidate_count": sum(1 for state in states if state.state == "necrosis_candidate"),
        "necrotic_archived_count": sum(1 for state in states if state.state == "necrotic_archived"),
        "replacement_root_count": sum(1 for state in states if state.state == "replacement"),
        "stable_root_count": sum(1 for state in states if state.state == "stable"),
    }
