from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.shadow_promotion import ShadowPromotionConfig, evaluate_shadow_promotion
from jianmu.self_learning.darwinforge.local_nutrient_cycle import make_test_colony


def test_shadow_promotion_does_not_modify_global_population_by_default():
    population = LayerPreservedPopulation.initialize(population_per_layer=2, seed=1)
    before = _weights_snapshot(population)
    colony = make_test_colony()
    colony.colony_stability_score = 3.0
    colony.local_prior_updates = [{"layer_name": "slot_binding_policy", "option": "surface_number_order", "weight_updates": {"number_count": 10}}]
    evaluate_shadow_promotion(colony, population, [], [], ShadowPromotionConfig(real_promotion_enabled=False))
    assert _weights_snapshot(population) == before


def test_shadow_promotion_rolls_back_on_global_regression():
    population = LayerPreservedPopulation.initialize(population_per_layer=2, seed=1)
    colony = make_test_colony()
    colony.toxicity_score = 5.0
    result = evaluate_shadow_promotion(colony, population)
    assert result.promotion_decision == "rollback"


def test_shadow_promotion_rolls_back_on_ood_regression():
    population = LayerPreservedPopulation.initialize(population_per_layer=2, seed=1)
    colony = make_test_colony()
    colony.colony_stability_score = 1.0
    colony.toxicity_score = 3.0
    result = evaluate_shadow_promotion(colony, population)
    assert result.ood_delta > 0
    assert result.promotion_decision == "rollback"


def _weights_snapshot(population):
    return {
        layer: [(neuron.option, dict(neuron.weights)) for neuron in neurons]
        for layer, neurons in population.per_layer.items()
    }
