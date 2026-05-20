from jianmu.self_learning.darwinforge.colony_lifecycle import update_colony_lifecycle
from jianmu.self_learning.darwinforge.nutrient_zone import NutrientZone
from jianmu.self_learning.darwinforge.root_colony import initialize_colonies


def test_colony_lifecycle_reports_tip_states():
    colony = initialize_colonies([NutrientZone("z", "slot", "", {}, "", "", "", "")])[0]

    metrics = update_colony_lifecycle([colony])

    assert metrics["events"]
    assert metrics["total_active_roots"] == 1
