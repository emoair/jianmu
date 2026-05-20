from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ResourceGrowthConfig:
    max_total_active_roots: int = 512
    max_roots_per_colony: int = 32
    max_new_tips_per_nourished_root: int = 4
    max_replacement_roots_per_generation: int = 64
    nutrient_bonus_budget: float = 2.0
    toxicity_penalty_budget: float = 4.0
    starvation_patience: int = 3
    default_ttl: int = 5
    max_ttl: int = 12


def allocate_root_resources(colonies: List, config: ResourceGrowthConfig) -> Dict:
    total_active = 0
    released = 0
    quarantined = 0
    distribution = {}
    for colony in colonies:
        active = [tip for tip in colony.root_tips if tip.state not in {"necrotic_archived"}]
        if colony.toxicity_score > colony.colony_stability_score:
            colony.local_resource_budget = max(1, colony.local_resource_budget // 2)
            colony_promotion_state = "quarantined"
            quarantined += 1
        else:
            colony_promotion_state = "local_only"
        if len(active) > config.max_roots_per_colony:
            overflow = active[config.max_roots_per_colony :]
            for tip in overflow:
                tip.state = "necrotic_archived"
                colony.necrotic_archive.append(tip)
                released += 1
        active_count = sum(1 for tip in colony.root_tips if tip.state not in {"necrotic_archived"})
        total_active += active_count
        distribution[colony.colony_id] = min(config.max_roots_per_colony, colony.local_resource_budget)
        colony.promotion_state = colony_promotion_state
    if total_active > config.max_total_active_roots:
        released += total_active - config.max_total_active_roots
        total_active = config.max_total_active_roots
    return {
        "total_active_roots": total_active,
        "resource_budget_used": sum(distribution.values()),
        "resource_released_count": released,
        "colony_budget_distribution": distribution,
        "quarantined_colony_count": quarantined,
    }
