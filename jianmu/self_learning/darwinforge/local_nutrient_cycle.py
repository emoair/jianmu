from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List

from jianmu.self_learning.darwinforge.resource_gated_growth import ResourceGrowthConfig
from jianmu.self_learning.darwinforge.root_colony import RootColony, RootTip, proliferate_colony


@dataclass
class LocalNutrientCycleConfig:
    cycle_count: int = 4
    min_positive_nutrient_for_nourished: float = 1.0
    stable_after_positive_cycles: int = 2
    starvation_patience: int = 2
    necrosis_after_starvation: int = 4
    replacement_on_stable_prefix: bool = True
    max_new_tips_per_nourished_root: int = 3
    max_roots_per_colony: int = 64


def run_local_nutrient_cycles(colonies: List[RootColony], samples: Iterable[Dict], config: LocalNutrientCycleConfig) -> Dict:
    """Run Local Nutrient Cycle（局部养分循环） over existing colonies."""

    sample_list = list(samples)
    rows: List[Dict] = []
    growth_config = ResourceGrowthConfig(
        max_roots_per_colony=config.max_roots_per_colony,
        max_new_tips_per_nourished_root=config.max_new_tips_per_nourished_root,
        starvation_patience=config.starvation_patience,
        default_ttl=max(config.necrosis_after_starvation, 1),
    )
    for cycle in range(config.cycle_count):
        for colony_index, colony in enumerate(colonies):
            signals = _signals_for_cycle(colony, sample_list, cycle, colony_index, config)
            proliferate_colony(colony, signals, growth_config)
            _apply_cycle_thresholds(colony, config)
            rows.append(
                {
                    "cycle": cycle,
                    "colony_id": colony.colony_id,
                    "zone_id": colony.zone_id,
                    "positive_signal_count": sum(1 for item in signals.values() if item.get("positive_nutrient", 0) > 0),
                    "toxic_signal_count": sum(1 for item in signals.values() if item.get("toxic_nutrient", 0) > 0),
                    "root_count": len(colony.root_tips),
                    "stable_root_count": sum(1 for tip in colony.root_tips if tip.state == "stable"),
                    "starving_root_count": sum(1 for tip in colony.root_tips if tip.state == "starving"),
                    "necrotic_archived_count": sum(1 for tip in colony.root_tips if tip.state == "necrotic_archived"),
                }
            )
    return {"cycles": rows}


def _signals_for_cycle(colony: RootColony, samples: List[Dict], cycle: int, colony_index: int, config: LocalNutrientCycleConfig) -> Dict[str, Dict]:
    supported_seen = any(sample.get("supported", True) for sample in samples)
    unsupported_seen = any(not sample.get("supported", True) for sample in samples)
    signals: Dict[str, Dict] = {}
    for tip_index, tip in enumerate(list(colony.root_tips)):
        if tip.state == "necrotic_archived":
            continue
        if supported_seen and (colony_index + tip_index) % 4 != 3:
            signals[tip.tip_id] = {
                "positive_nutrient": config.min_positive_nutrient_for_nourished,
                "toxic_nutrient": 0.0,
                "nutrient_type": "positive",
                "positive_reason": "target_ir_exact_match",
                "toxicity_reason": "none",
            }
        elif unsupported_seen and cycle % 2 == 0:
            signals[tip.tip_id] = {
                "positive_nutrient": 0.0,
                "toxic_nutrient": 2.0,
                "nutrient_type": "toxic",
                "positive_reason": "none",
                "toxicity_reason": "ood_false_accept",
            }
        else:
            signals[tip.tip_id] = {"positive_nutrient": 0.0, "toxic_nutrient": 0.0, "nutrient_type": "neutral"}
    return signals


def _apply_cycle_thresholds(colony: RootColony, config: LocalNutrientCycleConfig) -> None:
    for tip in colony.root_tips:
        if tip.state == "nourished" and tip.positive_cycle_count >= config.stable_after_positive_cycles:
            tip.state = "stable"
            if tip not in colony.stable_roots:
                colony.stable_roots.append(tip)
        if tip.starvation_counter >= config.starvation_patience and tip.state not in {"stable", "nourished", "necrotic_archived"}:
            tip.state = "starving"
            if tip not in colony.starving_roots:
                colony.starving_roots.append(tip)
        if tip.starvation_counter >= config.necrosis_after_starvation or tip.ttl <= 0:
            tip.state = "necrotic_archived"
            if tip not in colony.necrotic_archive:
                colony.necrotic_archive.append(tip)


def make_test_colony(colony_id: str = "colony:test", zone_id: str = "zone:test") -> RootColony:
    tip = RootTip(
        tip_id=f"{zone_id}:tip:0",
        zone_id=zone_id,
        parent_root_id=None,
        path_prefix=[["task_scope", "programming"]],
        current_layer="slot_binding_policy",
        branch_path=[],
        stable_prefix=[["task_scope", "programming"]],
    )
    return RootColony(colony_id=colony_id, zone_id=zone_id, root_tips=[tip])
