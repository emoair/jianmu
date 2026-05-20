from jianmu.self_learning.darwinforge.colony_memory import update_colony_memory
from jianmu.self_learning.darwinforge.nutrient_zone import NutrientZone
from jianmu.self_learning.darwinforge.root_colony import initialize_colonies


def test_colony_memory_records_positive_and_toxic_events():
    colony = initialize_colonies([NutrientZone("z", "slot", "", {}, "", "", "", "")])[0]
    candidates = [{"root_id": "r1", "sample_id": "s1", "zone_id": "z"}, {"root_id": "r2", "sample_id": "s2", "zone_id": "z"}]
    signals = {"r1": {"positive_nutrient": 1.0, "toxic_nutrient": 0.0}, "r2": {"positive_nutrient": 0.0, "toxic_nutrient": 3.0}}

    memory = update_colony_memory([colony], candidates, signals)

    assert memory.positive_memory
    assert memory.toxic_memory
