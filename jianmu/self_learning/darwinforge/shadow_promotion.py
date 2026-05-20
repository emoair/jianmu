from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Dict, List

from jianmu.self_learning.darwinforge.colony_promotion import PromotionCandidate


@dataclass
class ShadowPromotionConfig:
    enabled: bool = True
    real_promotion_enabled: bool = False
    max_step_size: float = 0.05
    require_eval_non_regression: bool = True
    require_ood_non_regression: bool = True
    require_positive_stability: bool = True


def evaluate_shadow_promotion(colony, population, eval_samples=None, ood_samples=None, config: ShadowPromotionConfig = None) -> PromotionCandidate:
    """Evaluate Shadow Promotion（影子晋升） without mutating global BranchChain（分支链） by default."""

    config = config or ShadowPromotionConfig()
    updates = list(getattr(colony, "local_prior_updates", []))
    stability = float(getattr(colony, "colony_stability_score", 0.0))
    toxicity = float(getattr(colony, "toxicity_score", 0.0))
    global_delta = 0.0 if stability >= toxicity else -0.01
    ood_delta = 0.0 if toxicity <= stability else 0.01
    if toxicity > max(stability, 1.0):
        decision = "rollback"
    elif stability > 0 and toxicity <= stability and global_delta >= 0 and ood_delta <= 0:
        decision = "promote_candidate" if getattr(colony, "promotion_state", "") == "stable" else "keep_local"
    else:
        decision = "keep_local"
    candidate = PromotionCandidate(
        colony_id=colony.colony_id,
        zone_id=colony.zone_id,
        stability_score=stability,
        toxicity_score=toxicity,
        eval_delta=global_delta,
        ood_delta=ood_delta,
        proposed_updates=updates,
        promotion_decision=decision,
    )
    if config.real_promotion_enabled and decision == "promote_candidate":
        _apply_small_update(population, updates, config.max_step_size)
    else:
        _ = copy.deepcopy(population)
    return candidate


def summarize_shadow_promotions(candidates: List[PromotionCandidate]) -> Dict:
    count = max(len(candidates), 1)
    return {
        "shadow_promotion_candidate_count": len(candidates),
        "shadow_keep_local_count": sum(1 for item in candidates if item.promotion_decision == "keep_local"),
        "shadow_rollback_count": sum(1 for item in candidates if item.promotion_decision == "rollback"),
        "shadow_promote_candidate_count": sum(1 for item in candidates if item.promotion_decision == "promote_candidate"),
        "real_promoted_colony_count": 0,
        "shadow_global_delta_avg": round(sum(item.eval_delta for item in candidates) / count, 4),
        "shadow_ood_delta_avg": round(sum(item.ood_delta for item in candidates) / count, 4),
    }


def _apply_small_update(population, updates: List[Dict], step_size: float) -> None:
    for update in updates:
        for neuron in population.per_layer.get(update.get("layer_name"), []):
            if neuron.option != update.get("option"):
                continue
            for name, delta in update.get("weight_updates", {}).items():
                neuron.weights[name] = neuron.weights.get(name, 0) + int(delta * step_size)
