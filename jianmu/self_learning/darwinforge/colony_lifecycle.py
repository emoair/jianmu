from __future__ import annotations

from typing import Dict, List

from jianmu.self_learning.darwinforge.root_colony import RootColony, summarize_colonies


def update_colony_lifecycle(colonies: List[RootColony]) -> Dict:
    events = []
    for colony in colonies:
        for tip in colony.root_tips:
            events.append({"colony_id": colony.colony_id, "zone_id": colony.zone_id, "tip_id": tip.tip_id, "state": tip.state, "ttl": tip.ttl, "starvation_counter": tip.starvation_counter})
    return {**summarize_colonies(colonies), "events": events}
