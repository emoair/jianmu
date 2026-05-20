from jianmu.self_learning.darwinforge.nutrient_zone import NutrientZone
from jianmu.self_learning.darwinforge.resource_gated_growth import ResourceGrowthConfig
from jianmu.self_learning.darwinforge.root_colony import initialize_colonies, proliferate_colony


def _zone():
    return NutrientZone("z", "slot_binding_policy", "task_scope=programming", {}, "math", "addition", "binary", "surface")


def test_root_colony_initializes_active_roots():
    colonies = initialize_colonies([_zone()], ResourceGrowthConfig(max_roots_per_colony=4))

    assert len(colonies) == 1
    assert colonies[0].root_tips[0].state == "active"


def test_nourished_root_tip_proliferates_locally():
    colony = initialize_colonies([_zone()], ResourceGrowthConfig(max_roots_per_colony=4))[0]
    tip_id = colony.root_tips[0].tip_id

    proliferate_colony(colony, {tip_id: {"positive_nutrient": 2.0, "toxic_nutrient": 0.0}}, ResourceGrowthConfig(max_roots_per_colony=4, max_new_tips_per_nourished_root=2))

    assert len(colony.root_tips) > 1
    assert colony.colony_stability_score > 0


def test_starving_root_tip_moves_to_necrosis():
    colony = initialize_colonies([_zone()], ResourceGrowthConfig(default_ttl=1, starvation_patience=1))[0]

    proliferate_colony(colony, {}, ResourceGrowthConfig(default_ttl=1, starvation_patience=1))

    assert colony.root_tips[0].state == "necrotic_archived"


def test_necrotic_root_does_not_consume_budget():
    colony = initialize_colonies([_zone()], ResourceGrowthConfig(default_ttl=1, starvation_patience=1))[0]
    proliferate_colony(colony, {}, ResourceGrowthConfig(default_ttl=1, starvation_patience=1))

    active = [tip for tip in colony.root_tips if tip.state != "necrotic_archived"]

    assert not active
