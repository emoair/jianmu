import copy

from jianmu.self_learning.darwinforge.layer_clone import (
    LayerCloneConfig,
    clone_layer_population,
    promote_clone_to_layer,
)
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation


def test_clone_layer_population_copies_weights():
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=7)
    base = population.per_layer["task_scope"]
    clones = clone_layer_population(base, "task_scope", LayerCloneConfig(clone_count_per_layer=2, perturbation_scale=0.0), generation=0)

    assert len(clones) == 2
    assert clones[0].neurons is not base
    assert [n.option for n in clones[0].neurons] == [n.option for n in base]
    assert [n.weights for n in clones[0].neurons] == [n.weights for n in base]


def test_clone_layer_population_applies_seeded_perturbation():
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=7)
    base = population.per_layer["language_target"]
    config = LayerCloneConfig(clone_count_per_layer=1, perturbation_scale=0.25, seed=123)

    first = clone_layer_population(base, "language_target", config, generation=2)[0]
    second = clone_layer_population(base, "language_target", config, generation=2)[0]

    assert [n.weights for n in first.neurons] == [n.weights for n in second.neurons]
    assert any(n.weights != b.weights for n, b in zip(first.neurons, base))


def test_clone_does_not_modify_base_layer_before_promotion():
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=7)
    before = copy.deepcopy([n.weights for n in population.per_layer["semantic_domain"]])

    clone_layer_population(
        population.per_layer["semantic_domain"],
        "semantic_domain",
        LayerCloneConfig(clone_count_per_layer=2, perturbation_scale=0.3),
        generation=1,
    )

    assert [n.weights for n in population.per_layer["semantic_domain"]] == before


def test_promote_clone_updates_base_layer():
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=7)
    clone = clone_layer_population(
        population.per_layer["arithmetic_family"],
        "arithmetic_family",
        LayerCloneConfig(clone_count_per_layer=1, perturbation_scale=0.2),
        generation=1,
    )[0]
    clone_weights = [n.weights for n in clone.neurons]

    promoted = promote_clone_to_layer(population, clone, "arithmetic_family", base_metric=0.1, clone_metric=0.2, promote_margin=0.05)

    assert promoted is True
    assert clone.promoted is True
    assert [n.weights for n in population.per_layer["arithmetic_family"]] == clone_weights


def test_backtracking_uses_same_weights_plus_perturbation():
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=7)
    base = population.per_layer["structure_policy"]
    clones = clone_layer_population(
        base,
        "structure_policy",
        LayerCloneConfig(clone_count_per_layer=1, perturbation_scale=0.1, seed=42),
        generation=3,
    )

    assert [n.option for n in clones[0].neurons] == [n.option for n in base]
    assert any(clone_n.weights != base_n.weights for clone_n, base_n in zip(clones[0].neurons, base))
