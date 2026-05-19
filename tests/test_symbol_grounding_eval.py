from pathlib import Path

from jianmu.self_learning.branchchain.surface_features import extract_surface_features
from jianmu.self_learning.datasets.symbol_grounding import build_symbol_grounding_dataset
from jianmu.self_learning.darwinforge.population import LayerPreservedPopulation
from jianmu.self_learning.darwinforge.symbol_grounding_eval import evaluate_symbol_grounding


def test_surface_features_expose_raw_symbols():
    features = extract_surface_features("三加四")
    assert features["contains_zh_numeral_char"] is True
    assert "三" in features["zh_numeral_chars_present"]
    assert features["contains_zh_operator_word"] is True
    assert "加" in features["zh_operator_words_present"]


def test_surface_features_do_not_normalize_chinese_numbers():
    features = extract_surface_features("三加四")
    assert features["chinese_numbers"] == []
    assert features["signed_numbers"] == []
    assert "normalized_number_value" not in features
    assert "parsed_number_list" not in features


def test_surface_features_do_not_parse_operator_to_ir():
    features = extract_surface_features("三加四")
    assert features["operator_sequence"] == ""
    assert "parsed_operator" not in features
    assert "operator_to_ir" not in features


def test_symbol_slot_accuracy_after_prediction_only():
    samples = build_symbol_grounding_dataset(size=600, seed=42)["eval"][:40]
    metrics = evaluate_symbol_grounding(LayerPreservedPopulation.initialize(population_per_layer=4, seed=1), samples, top_k=2)
    assert "symbol_slot_accuracy" in metrics["symbol_metrics"]


def test_paired_arabic_zh_agreement_metric():
    samples = build_symbol_grounding_dataset(size=600, seed=42)["eval"][:80]
    metrics = evaluate_symbol_grounding(LayerPreservedPopulation.initialize(population_per_layer=4, seed=1), samples, top_k=2)
    assert "paired_arabic_zh_agreement" in metrics["symbol_metrics"]


def test_zh_number_false_reject_metric():
    samples = build_symbol_grounding_dataset(size=600, seed=42)["eval"]
    metrics = evaluate_symbol_grounding(LayerPreservedPopulation.initialize(population_per_layer=4, seed=1), samples, top_k=2)
    assert "zh_number_expression_false_reject_rate" in metrics["symbol_metrics"]


def test_no_expression_oracle_import_in_eval():
    source = Path("jianmu/self_learning/darwinforge/symbol_grounding_eval.py").read_text(encoding="utf-8")
    assert "expression_oracle" not in source
    assert "parse_controlled_expression" not in source

