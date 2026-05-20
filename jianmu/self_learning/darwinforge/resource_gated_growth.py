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
    keep_local_budget_count = 0
    nourished_bonus = 0
    starvation_decay = 0
    necrosis_released = 0
    distribution = {}
    for colony in colonies:
        active = [tip for tip in colony.root_tips if tip.state not in {"necrotic_archived"}]
        nourished = sum(1 for tip in active if tip.state in {"nourished", "stable"})
        starving = sum(1 for tip in active if tip.state == "starving")
        necrotic = sum(1 for tip in colony.root_tips if tip.state == "necrotic_archived")
        if colony.promotion_state == "keep_local":
            keep_local_budget_count += 1
        if colony.toxicity_score > colony.colony_stability_score * 2 and colony.toxicity_score > 0:
            colony.local_resource_budget = max(1, colony.local_resource_budget // 2)
            colony_promotion_state = "quarantined"
            quarantined += 1
        else:
            bonus = min(nourished * int(config.nutrient_bonus_budget), config.max_roots_per_colony)
            decay = min(starving * int(max(config.toxicity_penalty_budget, 1)), colony.local_resource_budget)
            colony.local_resource_budget = max(1, min(config.max_roots_per_colony, colony.local_resource_budget + bonus - decay))
            nourished_bonus += bonus
            starvation_decay += decay
            colony_promotion_state = colony.promotion_state if colony.promotion_state in {"keep_local", "stable"} else "local_only"
        if len(active) > config.max_roots_per_colony:
            overflow = active[config.max_roots_per_colony :]
            for tip in overflow:
                tip.state = "necrotic_archived"
                colony.necrotic_archive.append(tip)
                released += 1
        released += necrotic
        necrosis_released += necrotic
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
        "active_budget_used": total_active,
        "nourished_budget_bonus": nourished_bonus,
        "starvation_budget_decay": starvation_decay,
        "necrosis_budget_released": necrosis_released,
        "keep_local_budget_count": keep_local_budget_count,
        "quarantine_budget_reduced_count": quarantined,
        "colony_budget_distribution": distribution,
        "quarantined_colony_count": quarantined,
    }
