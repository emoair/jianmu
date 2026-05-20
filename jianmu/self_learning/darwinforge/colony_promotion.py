from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PromotionCandidate:
    colony_id: str
    zone_id: str
    stability_score: float
    toxicity_score: float
    eval_delta: float
    ood_delta: float
    proposed_updates: List[Dict] = field(default_factory=list)
    promotion_decision: str = "keep_local"

    def to_dict(self) -> Dict:
        return dict(self.__dict__)


def evaluate_colony_for_promotion(colony, heldout_eval=None, ood_samples=None, min_support: int = 2, stability_threshold: float = 3.0, toxicity_threshold: float = 1.0) -> PromotionCandidate:
    support = len(colony.stable_roots) + int(colony.colony_stability_score > 0)
    decision = "keep_local"
    if colony.toxicity_score > toxicity_threshold and colony.toxicity_score > colony.colony_stability_score:
        decision = "quarantine"
    elif support >= min_support and colony.colony_stability_score >= stability_threshold:
        decision = "promote"
    elif colony.colony_stability_score <= 0 and colony.toxicity_score <= 0:
        decision = "reject"
    updates = list(colony.local_prior_updates)
    return PromotionCandidate(
        colony_id=colony.colony_id,
        zone_id=colony.zone_id,
        stability_score=colony.colony_stability_score,
        toxicity_score=colony.toxicity_score,
        eval_delta=0.0,
        ood_delta=0.0,
        proposed_updates=updates,
        promotion_decision=decision,
    )


def apply_colony_promotion(population, promotion_candidate: PromotionCandidate, step_size: int = 1, global_delta: float = 0.0, ood_delta: float = 0.0) -> Dict:
    if promotion_candidate.promotion_decision != "promote":
        return {"applied": False, "rollback": False, "reason": promotion_candidate.promotion_decision}
    if global_delta < 0 or ood_delta > 0:
        promotion_candidate.promotion_decision = "rollback"
        return {"applied": False, "rollback": True, "reason": "global_or_ood_regression"}
    updated = 0
    for update in promotion_candidate.proposed_updates:
        for neuron in population.per_layer.get(update.get("layer_name"), []):
            if neuron.option != update.get("option"):
                continue
            for name, delta in update.get("weight_updates", {}).items():
                neuron.weights[name] = neuron.weights.get(name, 0) + int(delta * step_size)
            updated += 1
    return {"applied": True, "rollback": False, "updated_neuron_count": updated}


def summarize_promotions(candidates: List[PromotionCandidate], applications: List[Dict]) -> Dict:
    decisions = Counter(candidate.promotion_decision for candidate in candidates)
    return {
        "promotion_candidate_count": len(candidates),
        "promoted_colony_count": decisions.get("promote", 0),
        "keep_local_colony_count": decisions.get("keep_local", 0),
        "quarantined_colony_count": decisions.get("quarantine", 0),
        "rollback_count": sum(1 for item in applications if item.get("rollback")),
        "promotion_global_delta": 0.0,
        "promotion_ood_delta": 0.0,
    }
