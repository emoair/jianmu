from pathlib import Path

from jianmu.self_learning.darwinforge.path_prior_seeding import apply_path_prior_seeds, build_path_prior_seeds
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation


def _sample():
    return {
        "sample_id": "s-lit",
        "split": "train",
        "input_text": "49",
        "input_mode": "arabic_math_expression",
        "expression_family": "literal_only",
        "structure_policy": "literal_value",
        "number_count": 1,
        "operator_count": 0,
        "supported": True,
    }


def _score_diag():
    return {
        "sample_id": "s-lit",
        "score_diagnostic": {
            "layers": [
                {"layer_name": "arithmetic_family", "target_option": "literal_only"},
                {"layer_name": "structure_policy", "target_option": "literal_value"},
                {"layer_name": "target_builder", "target_option": "canonical_arithmetic_targetir"},
            ]
        },
    }


def test_path_prior_seed_does_not_use_targetir_as_feature():
    seeds = build_path_prior_seeds([_sample()], [{"sample_id": "s-lit", "exact_match": True}], [_score_diag()])

    assert seeds
    for seed in seeds:
        assert "target_ir" not in str(seed.feature_conditions)
        assert "expected_output" not in str(seed.feature_conditions)


def test_path_prior_seed_updates_branch_neurons():
    population = LayerPreservedPopulation.initialize(population_per_layer=8, seed=42)
    before = [dict(neuron.weights) for neuron in population.per_layer["arithmetic_family"] if neuron.option == "literal_only"][0]
    seeds = build_path_prior_seeds([_sample()], [{"sample_id": "s-lit", "exact_match": True}], [_score_diag()])

    metrics = apply_path_prior_seeds(population, seeds)

    after = [dict(neuron.weights) for neuron in population.per_layer["arithmetic_family"] if neuron.option == "literal_only"][0]
    assert metrics["branch_neuron_updated_count"] > 0
    assert after != before


def test_no_expression_oracle_import():
    source = Path("jianmu/self_learning/darwinforge/path_prior_seeding.py").read_text(encoding="utf-8")

    assert "expression_oracle" not in source
    assert "parse_controlled_expression" not in source
