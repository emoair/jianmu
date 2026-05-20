import inspect

from jianmu.self_learning.darwinforge.canonicalized_training_eval import (
    build_training_features,
    evaluate_canonicalized_training,
)
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.datasets.symbol_grounding import build_symbol_grounding_dataset


def _samples():
    splits = build_symbol_grounding_dataset(size=120, seed=11)
    return splits["train"] + splits["eval"] + splits["ood"]


def test_canonicalized_training_uses_canonical_text_for_features():
    features = build_training_features("三加四", canonicalization_enabled=True)
    assert features["canonical_text"] == "3+4"
    assert features["signed_numbers"] == [3, 4]
    assert features["operator_sequence"] == "+"


def test_raw_training_uses_raw_text_for_features():
    features = build_training_features("三加四", canonicalization_enabled=False)
    assert features["canonical_text"] == "三加四"
    assert features["signed_numbers"] == []
    assert features["operator_sequence"] == ""


def test_source_map_not_used_as_targetir():
    features = build_training_features("三加四", canonicalization_enabled=True)
    assert "source_map" not in features
    assert "target_ir_canonical" not in features
    assert "expected_output" not in features


def test_canonicalized_eval_outputs_required_metrics():
    population = LayerPreservedPopulation.initialize(population_per_layer=4, seed=2)
    metrics = evaluate_canonicalized_training(population, _samples()[:50], top_k=2, canonicalization_enabled=True)
    assert "overall" in metrics
    assert "candidate_generation_success_rate" in metrics["overall"]
    assert "zh_number_metrics" in metrics
    assert "known_diagnostics" in metrics


def test_canonicalized_eval_by_input_mode():
    population = LayerPreservedPopulation.initialize(population_per_layer=4, seed=2)
    metrics = evaluate_canonicalized_training(population, _samples()[:80], top_k=2, canonicalization_enabled=True)
    assert "by_input_mode" in metrics
    assert metrics["by_input_mode"]


def test_canonicalized_eval_by_curriculum_stage():
    population = LayerPreservedPopulation.initialize(population_per_layer=4, seed=2)
    metrics = evaluate_canonicalized_training(population, _samples()[:80], top_k=2, canonicalization_enabled=True)
    assert "by_curriculum_stage" in metrics
    assert metrics["by_curriculum_stage"]


def test_zh_number_false_reject_metric():
    population = LayerPreservedPopulation.initialize(population_per_layer=4, seed=2)
    metrics = evaluate_canonicalized_training(population, _samples()[:80], top_k=2, canonicalization_enabled=True)
    assert "zh_number_expression_false_reject_rate" in metrics["zh_number_metrics"]


def test_unsupported_arithmetic_false_accept_metric():
    population = LayerPreservedPopulation.initialize(population_per_layer=4, seed=2)
    metrics = evaluate_canonicalized_training(population, _samples(), top_k=2, canonicalization_enabled=True)
    assert "unsupported_arithmetic_false_accept_rate" in metrics["known_diagnostics"]


def test_no_expression_oracle_import_in_canonicalized_training_eval():
    import jianmu.self_learning.darwinforge.canonicalized_training_eval as module

    assert "expression_oracle" not in inspect.getsource(module)


def test_no_external_api_calls_in_canonicalized_training_eval():
    import jianmu.self_learning.darwinforge.canonicalized_training_eval as module

    source = inspect.getsource(module)
    assert "requests" not in source
    assert "httpx" not in source
    assert "openai" not in source.lower()

