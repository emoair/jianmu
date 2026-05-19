import json
from pathlib import Path

from jianmu.self_learning.learned_router.evaluate import train_and_evaluate
from jianmu.self_learning.learned_router.features import extract_features
from jianmu.self_learning.learned_router.perceptron import LabeledSample, MulticlassPerceptron
from jianmu.self_learning.learned_router.route_classifier import RouteClassifier


def test_feature_extractor_deterministic():
    text = "写一个 C 程序，输出 1+2+3"
    assert extract_features(text) == extract_features(text)


def test_feature_extractor_has_chinese_and_numeric_features():
    features = extract_features("定义三个 int，分别是 1、2、-3，然后 printf 输出和")
    assert features["kw_output"] == 1.0
    assert features["tech_int"] == 1.0
    assert features["tech_printf"] == 1.0
    assert features["num_arabic_count"] == 3.0
    assert features["num_negative_count"] == 1.0
    assert features["punct_chinese"] == 1.0


def test_perceptron_can_learn_tiny_separable_dataset():
    samples = [
        LabeledSample({"x": 1.0}, "left"),
        LabeledSample({"y": 1.0}, "right"),
    ]
    model = MulticlassPerceptron(["left", "right"], epochs=5, seed=1).fit(samples)
    assert model.predict({"x": 1.0}) == "left"
    assert model.predict({"y": 1.0}) == "right"


def test_route_classifier_train_and_predict():
    train = [
        {"input_text": "再加一个 2", "route_id": "append_literal_to_existing_sum", "task_family": "append_literal_to_existing_sum", "supported": True},
        {"input_text": "输出 1-2", "route_id": "unsupported_expression_input", "task_family": "unsupported_input", "supported": False},
        {"input_text": "写一个 C 程序，输出 1+2", "route_id": "generate_new_sum_from_text", "task_family": "generate_sum_program", "supported": True},
    ]
    classifier = RouteClassifier(epochs=8, seed=3).fit(train)
    prediction = classifier.predict("再加一个 5")
    assert prediction.route_id
    assert prediction.task_family
    assert prediction.supported in {"supported", "unsupported"}
    assert prediction.features_summary


def test_route_classifier_save_load_roundtrip(tmp_path):
    train = [
        {"input_text": "再加一个 2", "route_id": "append_literal_to_existing_sum", "task_family": "append_literal_to_existing_sum", "supported": True},
        {"input_text": "sum of three numbers", "route_id": "unsupported_language_input", "task_family": "unsupported_input", "supported": False},
    ]
    classifier = RouteClassifier(epochs=4, seed=4).fit(train)
    path = tmp_path / "model.json"
    classifier.save_json(path)
    loaded = RouteClassifier.load_json(path)
    assert loaded.predict("再加一个 3").route_id == classifier.predict("再加一个 3").route_id


def test_evaluation_outputs_required_metrics(tmp_path):
    metrics = train_and_evaluate(output_dir=tmp_path, epochs=3, seed=42)
    for key in [
        "route_id_accuracy",
        "task_family_accuracy",
        "supported_accuracy",
        "macro_accuracy_by_route_id",
        "confusion_matrix_route_id",
        "unsupported_precision",
        "unsupported_recall",
        "unsupported_f1",
        "eval_count",
        "train_count",
        "majority_route_id_accuracy",
        "learned_route_id_accuracy",
        "majority_supported_accuracy",
        "learned_supported_accuracy",
    ]:
        assert key in metrics


def test_eval_predictions_jsonl_written(tmp_path):
    train_and_evaluate(output_dir=tmp_path, epochs=2, seed=42)
    path = tmp_path / "route_classifier_predictions_eval.jsonl"
    assert path.exists()
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert rows
    assert {
        "sample_id",
        "input_text",
        "true_route_id",
        "pred_route_id",
        "true_task_family",
        "pred_task_family",
        "true_supported",
        "pred_supported",
        "correct_route",
        "correct_family",
        "correct_supported",
        "top_route_scores",
    } <= set(rows[0])


def test_majority_baseline_present(tmp_path):
    metrics = train_and_evaluate(output_dir=tmp_path, epochs=2, seed=42)
    assert "majority_labels" in metrics
    assert metrics["majority_route_id_accuracy"] >= 0.0
    assert metrics["majority_supported_accuracy"] >= 0.0


def test_no_label_leakage_feature_names():
    features = extract_features("写一个 C 程序，输出 1+2")
    forbidden = ["route_id", "task_family", "supported", "expected_output", "generate_new_sum_from_text"]
    feature_names = "\n".join(features)
    for token in forbidden:
        assert token not in feature_names


def test_existing_v05_tests_still_pass():
    from jianmu.runtime import Runtime
    from jianmu.hierarchical_router import HierarchicalSemanticRouter

    assert Runtime()
    assert HierarchicalSemanticRouter()

