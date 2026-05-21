from jianmu.self_learning.darwinforge.nutrient_zone import NutrientZone
from jianmu.self_learning.darwinforge.resource_gated_growth import ResourceGrowthConfig
from jianmu.self_learning.darwinforge.root_colony import initialize_colonies, proliferate_colony
from jianmu.self_learning.darwinforge.trained_root_colony_capture import TrainedRootColonyState, capture_trained_root_colonies


def _colonies():
    zones = [NutrientZone("z1", "support_gate", "task_scope=programming", {}, "boundary", "", "", "")]
    colonies = initialize_colonies(zones, ResourceGrowthConfig(max_roots_per_colony=8))
    for colony in colonies:
        proliferate_colony(colony, {tip.tip_id: {"positive_nutrient": 1.0} for tip in colony.root_tips}, ResourceGrowthConfig(max_roots_per_colony=8))
    return colonies


def test_trained_root_colony_roundtrip():
    state = capture_trained_root_colonies(_colonies())
    restored = TrainedRootColonyState.from_dict(state.to_dict())
    assert restored.compute_hash(without_hash=True) == state.to_dict()["state_hash"]
    assert restored.colony_count == 1


def test_runtime_state_capture_records_root_colonies():
    state = capture_trained_root_colonies(_colonies())
    assert state.root_count >= 1
    assert state.resource_budget_state
