from jianmu.self_learning.darwinforge.nutrient_zone import NutrientZone
from jianmu.self_learning.darwinforge.resource_gated_growth import ResourceGrowthConfig, allocate_root_resources
from jianmu.self_learning.darwinforge.root_colony import initialize_colonies


def test_resource_gated_growth_limits_total_roots():
    zone = NutrientZone("z", "slot", "", {}, "", "", "", "")
    colony = initialize_colonies([zone], ResourceGrowthConfig(max_roots_per_colony=2))[0]
    colony.root_tips.extend([colony.root_tips[0], colony.root_tips[0]])

    metrics = allocate_root_resources([colony], ResourceGrowthConfig(max_total_active_roots=1, max_roots_per_colony=1))

    assert metrics["total_active_roots"] <= 1


def test_resource_gated_growth_quarantines_toxic_colony():
    zone = NutrientZone("z", "slot", "", {}, "", "", "", "")
    colony = initialize_colonies([zone], ResourceGrowthConfig())[0]
    colony.toxicity_score = 5

    metrics = allocate_root_resources([colony], ResourceGrowthConfig())

    assert metrics["quarantined_colony_count"] == 1
