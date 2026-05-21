from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.trained_branch_population_capture import TrainedBranchPopulationState, capture_trained_branch_population


def test_trained_branch_population_roundtrip():
    population = LayerPreservedPopulation.initialize(population_per_layer=12, seed=7)
    state = capture_trained_branch_population(population)
    restored = TrainedBranchPopulationState.from_dict(state.to_dict())
    assert restored.compute_hash(without_hash=True) == state.to_dict()["state_hash"]
    assert restored.branch_neuron_states


def test_runtime_state_capture_records_branch_population():
    population = LayerPreservedPopulation.initialize(population_per_layer=10, seed=42)
    state = capture_trained_branch_population(population)
    assert state.to_dict()["layer_states"]
    assert all("target_ir" not in row for row in state.to_dict()["branch_neuron_states"])
