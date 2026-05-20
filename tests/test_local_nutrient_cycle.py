from jianmu.self_learning.darwinforge.local_nutrient_cycle import LocalNutrientCycleConfig, make_test_colony, run_local_nutrient_cycles
from jianmu.self_learning.darwinforge.resource_gated_growth import ResourceGrowthConfig, allocate_root_resources
from jianmu.self_learning.darwinforge.root_colony import proliferate_colony


def test_local_nutrient_cycle_marks_nourished_root():
    colony = make_test_colony()
    proliferate_colony(colony, {colony.root_tips[0].tip_id: {"positive_nutrient": 1.0}}, ResourceGrowthConfig())
    assert any(tip.state in {"nourished", "stable"} for tip in colony.root_tips)


def test_local_nutrient_cycle_marks_stable_after_repeated_positive():
    colony = make_test_colony()
    cfg = ResourceGrowthConfig()
    for _ in range(2):
        proliferate_colony(colony, {colony.root_tips[0].tip_id: {"positive_nutrient": 1.0}}, cfg)
    assert any(tip.state == "stable" for tip in colony.root_tips)


def test_local_nutrient_cycle_marks_starving_without_nutrient():
    colony = make_test_colony()
    proliferate_colony(colony, {colony.root_tips[0].tip_id: {}}, ResourceGrowthConfig(starvation_patience=3))
    assert any(tip.state == "starving" for tip in colony.root_tips)


def test_local_nutrient_cycle_archives_necrotic_root():
    colony = make_test_colony()
    colony.root_tips[0].ttl = 1
    cfg = ResourceGrowthConfig(starvation_patience=2, default_ttl=1)
    proliferate_colony(colony, {colony.root_tips[0].tip_id: {}}, cfg)
    assert any(tip.state == "necrotic_archived" for tip in colony.root_tips)


def test_local_nutrient_cycle_creates_replacement_from_stable_prefix():
    colony = make_test_colony()
    cfg = ResourceGrowthConfig(starvation_patience=4)
    for _ in range(2):
        proliferate_colony(colony, {colony.root_tips[0].tip_id: {}}, cfg)
    assert colony.replacement_queue


def test_resource_gated_growth_releases_necrotic_budget():
    colony = make_test_colony()
    colony.root_tips[0].state = "necrotic_archived"
    metrics = allocate_root_resources([colony], ResourceGrowthConfig())
    assert metrics["necrosis_budget_released"] >= 1


def test_resource_gated_growth_bonus_for_nourished_roots():
    colony = make_test_colony()
    colony.root_tips[0].state = "nourished"
    metrics = allocate_root_resources([colony], ResourceGrowthConfig(max_roots_per_colony=64))
    assert metrics["nourished_budget_bonus"] > 0


def test_local_nutrient_cycle_runs_multiple_cycles():
    colony = make_test_colony()
    payload = run_local_nutrient_cycles([colony], [{"supported": True}], LocalNutrientCycleConfig(cycle_count=4))
    assert len(payload["cycles"]) == 4
