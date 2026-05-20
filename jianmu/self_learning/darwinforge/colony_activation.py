from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from jianmu.self_learning.darwinforge.local_nutrient_cycle import LocalNutrientCycleConfig, run_local_nutrient_cycles
from jianmu.self_learning.darwinforge.root_colony import RootColony


@dataclass
class ColonyActivationResult:
    colony_id: str
    zone_id: str
    cycle_count: int
    positive_nutrient_count: int
    toxic_nutrient_count: int
    neutral_count: int
    nourished_root_count: int
    stable_root_count: int
    starving_root_count: int
    necrotic_archived_count: int
    replacement_root_count: int
    colony_stability_score: float
    colony_toxicity_score: float
    activation_state: str

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def activate_colonies(colonies: List[RootColony], train_samples: List[Dict], ood_samples: List[Dict], config: LocalNutrientCycleConfig) -> List[ColonyActivationResult]:
    """Activate Colony Nutrient Activation（根群养分激活） before global promotion."""

    cycle_payload = run_local_nutrient_cycles(colonies, train_samples + ood_samples, config)
    cycle_by_colony: Dict[str, List[Dict]] = {}
    for row in cycle_payload["cycles"]:
        cycle_by_colony.setdefault(row["colony_id"], []).append(row)
    results = []
    for colony in colonies:
        rows = cycle_by_colony.get(colony.colony_id, [])
        positive_count = sum(row.get("positive_signal_count", 0) for row in rows)
        toxic_count = sum(row.get("toxic_signal_count", 0) for row in rows)
        neutral_count = max(0, len(rows) - positive_count - toxic_count)
        nourished = sum(1 for tip in colony.root_tips if tip.state == "nourished")
        stable = sum(1 for tip in colony.root_tips if tip.state == "stable")
        starving = sum(1 for tip in colony.root_tips if tip.state == "starving")
        necrotic = sum(1 for tip in colony.root_tips if tip.state == "necrotic_archived")
        replacement = len(colony.replacement_queue)
        state = _activation_state(positive_count, toxic_count, stable, colony.colony_stability_score, colony.toxicity_score)
        colony.promotion_state = state
        results.append(
            ColonyActivationResult(
                colony_id=colony.colony_id,
                zone_id=colony.zone_id,
                cycle_count=config.cycle_count,
                positive_nutrient_count=positive_count,
                toxic_nutrient_count=toxic_count,
                neutral_count=neutral_count,
                nourished_root_count=nourished,
                stable_root_count=stable,
                starving_root_count=starving,
                necrotic_archived_count=necrotic,
                replacement_root_count=replacement,
                colony_stability_score=round(colony.colony_stability_score, 4),
                colony_toxicity_score=round(colony.toxicity_score, 4),
                activation_state=state,
            )
        )
    return results


def summarize_activation(results: List[ColonyActivationResult]) -> Dict:
    return {
        "activated_colony_count": sum(1 for item in results if item.activation_state in {"active", "nourished", "stable", "keep_local"}),
        "keep_local_colony_count": sum(1 for item in results if item.activation_state == "keep_local"),
        "stable_colony_count": sum(1 for item in results if item.activation_state == "stable"),
        "quarantined_colony_count": sum(1 for item in results if item.activation_state == "quarantine"),
        "rejected_colony_count": sum(1 for item in results if item.activation_state == "reject"),
    }


def _activation_state(positive_count: int, toxic_count: int, stable_root_count: int, stability: float, toxicity: float) -> str:
    if toxicity >= max(stability, 1.0) * 2 or toxic_count >= max(positive_count, 1) * 2:
        return "quarantine"
    if stable_root_count > 0 and positive_count > 0 and toxic_count == 0:
        return "stable"
    if positive_count > 0 and toxicity <= max(stability, 1.0):
        return "keep_local"
    if positive_count > 0:
        return "nourished"
    return "reject"
