from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from jianmu.self_learning.darwinforge.resource_gated_growth import ResourceGrowthConfig


@dataclass
class RootTip:
    tip_id: str
    zone_id: str
    parent_root_id: Optional[str]
    path_prefix: List[List[str]]
    current_layer: str
    branch_path: List[List[str]]
    confidence_history: List[float] = field(default_factory=list)
    nutrient_history: List[float] = field(default_factory=list)
    toxicity_history: List[float] = field(default_factory=list)
    starvation_counter: int = 0
    ttl: int = 5
    state: str = "active"

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


@dataclass
class RootColony:
    colony_id: str
    zone_id: str
    root_tips: List[RootTip] = field(default_factory=list)
    stable_roots: List[RootTip] = field(default_factory=list)
    starving_roots: List[RootTip] = field(default_factory=list)
    necrotic_archive: List[RootTip] = field(default_factory=list)
    replacement_queue: List[RootTip] = field(default_factory=list)
    local_resource_budget: int = 32
    local_prior_updates: List[Dict] = field(default_factory=list)
    colony_stability_score: float = 0.0
    toxicity_score: float = 0.0
    promotion_state: str = "local_only"

    def to_dict(self) -> Dict:
        payload = dict(self.__dict__)
        payload["root_tips"] = [tip.to_dict() for tip in self.root_tips]
        payload["stable_roots"] = [tip.tip_id for tip in self.stable_roots]
        payload["starving_roots"] = [tip.tip_id for tip in self.starving_roots]
        payload["necrotic_archive"] = [tip.tip_id for tip in self.necrotic_archive]
        payload["replacement_queue"] = [tip.tip_id for tip in self.replacement_queue]
        return payload


def initialize_colonies(zones, config: ResourceGrowthConfig = None) -> List[RootColony]:
    config = config or ResourceGrowthConfig()
    colonies = []
    for zone in zones:
        tip = RootTip(
            tip_id=f"{zone.zone_id}:tip:0",
            zone_id=zone.zone_id,
            parent_root_id=None,
            path_prefix=[part.split("=", 1) for part in zone.stable_prefix_signature.split(">") if "=" in part],
            current_layer=zone.fork_layer,
            branch_path=[],
            ttl=config.default_ttl,
        )
        colonies.append(RootColony(colony_id=f"colony:{zone.zone_id}", zone_id=zone.zone_id, root_tips=[tip], local_resource_budget=config.max_roots_per_colony))
    return colonies


def proliferate_colony(colony: RootColony, nutrient_signals: Dict[str, Dict], config: ResourceGrowthConfig) -> RootColony:
    new_tips = []
    for tip in list(colony.root_tips):
        signal = nutrient_signals.get(tip.tip_id, {})
        positive = float(signal.get("positive_nutrient", 0.0))
        toxic = float(signal.get("toxic_nutrient", 0.0))
        tip.nutrient_history.append(positive)
        tip.toxicity_history.append(toxic)
        if toxic > 0:
            tip.toxicity_history.append(toxic)
            tip.starvation_counter += 2
            tip.state = "necrosis_candidate"
            colony.toxicity_score += toxic
        elif positive > 0:
            tip.starvation_counter = 0
            tip.ttl = min(config.max_ttl, tip.ttl + 1)
            tip.state = "stable" if sum(1 for value in tip.nutrient_history[-3:] if value > 0) >= 3 else "nourished"
            colony.colony_stability_score += positive
            if len(colony.root_tips) + len(new_tips) < colony.local_resource_budget:
                for index in range(min(config.max_new_tips_per_nourished_root, colony.local_resource_budget - len(colony.root_tips) - len(new_tips))):
                    child = RootTip(
                        tip_id=f"{tip.tip_id}:split:{len(new_tips)}:{index}",
                        zone_id=tip.zone_id,
                        parent_root_id=tip.tip_id,
                        path_prefix=list(tip.path_prefix),
                        current_layer=tip.current_layer,
                        branch_path=list(tip.branch_path),
                        ttl=config.default_ttl,
                        state="active",
                    )
                    new_tips.append(child)
        else:
            tip.starvation_counter += 1
            tip.ttl -= 1
            tip.state = "starving"
        if tip.starvation_counter >= config.starvation_patience or tip.ttl <= 0:
            tip.state = "necrotic_archived"
            colony.necrotic_archive.append(tip)
        elif tip.state == "stable" and tip not in colony.stable_roots:
            colony.stable_roots.append(tip)
        elif tip.state == "starving" and tip not in colony.starving_roots:
            colony.starving_roots.append(tip)
    colony.root_tips.extend(new_tips)
    colony.root_tips = colony.root_tips[: colony.local_resource_budget]
    return colony


def summarize_colonies(colonies: List[RootColony]) -> Dict:
    tips = [tip for colony in colonies for tip in colony.root_tips]
    return {
        "colony_count": len(colonies),
        "total_active_roots": sum(1 for tip in tips if tip.state not in {"necrotic_archived"}),
        "nourished_root_count": sum(1 for tip in tips if tip.state == "nourished"),
        "starving_root_count": sum(1 for tip in tips if tip.state == "starving"),
        "necrotic_archived_count": sum(1 for tip in tips if tip.state == "necrotic_archived"),
        "replacement_root_count": sum(len(colony.replacement_queue) for colony in colonies),
        "stable_root_count": sum(1 for tip in tips if tip.state == "stable"),
    }
