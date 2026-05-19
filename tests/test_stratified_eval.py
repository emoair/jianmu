from jianmu.self_learning.datasets.large_architecture_aligned import build_large_architecture_aligned_dataset
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.stratified_eval import evaluate_dataset_stratified


def _samples():
    splits = build_large_architecture_aligned_dataset(size=800, seed=42)
    rows = []
    for split in splits.values():
        rows.extend(split)
    return rows[:120]


def test_stratified_eval_outputs_required_metrics():
    metrics = evaluate_dataset_stratified(LayerPreservedPopulation.initialize(population_per_layer=4, seed=1), _samples(), top_k=2)
    required = {
        "sample_count",
        "supported_count",
        "unsupported_count",
        "target_ir_exact_match",
        "expected_output_match",
        "unsupported_rejection_rate",
        "false_reject_supported_rate",
        "false_accept_unsupported_rate",
        "candidate_generation_success_rate",
        "true_missing_layer_rate",
        "early_reject_short_path_rate",
    }
    assert required <= set(metrics["overall"])


def test_stratified_eval_by_input_mode():
    metrics = evaluate_dataset_stratified(LayerPreservedPopulation.initialize(population_per_layer=4, seed=1), _samples(), top_k=2)
    assert metrics["by_input_mode"]
    assert "zh_technical_mixed" in metrics["by_input_mode"]


def test_stratified_eval_by_expression_family():
    metrics = evaluate_dataset_stratified(LayerPreservedPopulation.initialize(population_per_layer=4, seed=1), _samples(), top_k=2)
    assert metrics["by_expression_family"]
    assert any(key in metrics["by_expression_family"] for key in ["addition", "multiplication", "subtraction"])


def test_zh_number_expression_false_reject_metric():
    samples = [sample for sample in _samples() if sample["input_mode"] == "zh_number_expression"][:10]
    metrics = evaluate_dataset_stratified(LayerPreservedPopulation.initialize(population_per_layer=4, seed=1), samples, top_k=2)
    assert "zh_number_expression_false_reject_rate" in metrics["diagnostics"]


def test_unsupported_arithmetic_false_accept_metric():
    samples = [sample for sample in build_large_architecture_aligned_dataset(size=800, seed=42)["eval_ood"] if sample["input_mode"] == "unsupported_arithmetic"][:10]
    metrics = evaluate_dataset_stratified(LayerPreservedPopulation.initialize(population_per_layer=4, seed=1), samples, top_k=2)
    assert "unsupported_arithmetic_false_accept_rate" in metrics["diagnostics"]

