from jianmu.self_learning.darwinforge.colony_promotion import apply_colony_promotion, evaluate_colony_for_promotion
from jianmu.self_learning.darwinforge.nutrient_zone import NutrientZone
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.root_colony import initialize_colonies


def _colony(stability=5, toxicity=0):
    colony = initialize_colonies([NutrientZone("z", "slot", "", {}, "", "", "", "")])[0]
    colony.colony_stability_score = stability
    colony.toxicity_score = toxicity
    colony.stable_roots.append(colony.root_tips[0])
    colony.local_prior_updates = [{"layer_name": "slot_binding_policy", "option": "surface_number_order", "weight_updates": {"number_count": 1}}]
    return colony


def test_colony_promotion_requires_low_toxicity():
    candidate = evaluate_colony_for_promotion(_colony(stability=5, toxicity=9))

    assert candidate.promotion_decision == "quarantine"


def test_colony_promotion_rolls_back_on_global_regression():
    candidate = evaluate_colony_for_promotion(_colony())
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=42)

    result = apply_colony_promotion(population, candidate, global_delta=-0.1, ood_delta=0.0)

    assert result["rollback"] is True


def test_colony_promotion_rolls_back_on_ood_regression():
    candidate = evaluate_colony_for_promotion(_colony())
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=43)

    result = apply_colony_promotion(population, candidate, global_delta=0.0, ood_delta=0.1)

    assert result["rollback"] is True
