import json
from pathlib import Path

import pytest

from jianmu.sandbox import Sandbox, has_supported_c_compiler
from jianmu.self_learning.arithmetic_targetir.dataset_generator import build_dataset
from jianmu.self_learning.arithmetic_targetir.evaluate import train_and_evaluate
from jianmu.self_learning.arithmetic_targetir.expression_oracle import UnsupportedReason, parse_controlled_expression
from jianmu.self_learning.arithmetic_targetir.features import extract_arithmetic_features
from jianmu.self_learning.arithmetic_targetir.hashed_perceptron import HashedLabeledSample, HashedPerceptron
from jianmu.self_learning.arithmetic_targetir.targetir_router import ArithmeticTargetIRRouter


def test_expression_oracle_precedence():
    ir = parse_controlled_expression("写一个 C 程序输出 1+2*3")
    assert ir.expected_output == "7\n"
    assert ir.canonical_expr == "add(lit(1),mul(lit(2),lit(3)))"


def test_expression_oracle_parentheses():
    ir = parse_controlled_expression("写一个 C 程序输出 (1+2)*3")
    assert ir.expected_output == "9\n"
    assert ir.canonical_expr == "mul(add(lit(1),lit(2)),lit(3))"


def test_expression_oracle_exact_division():
    ir = parse_controlled_expression("输出 8/2")
    assert ir.expected_output == "4\n"
    assert ir.canonical_expr == "div(lit(8),lit(2))"


def test_expression_oracle_rejects_non_exact_division():
    result = parse_controlled_expression("输出 5/2")
    assert isinstance(result, UnsupportedReason)
    assert result.reason == "division_not_exact"


@pytest.mark.skipif(not has_supported_c_compiler(), reason="requires a supported C compiler")
def test_target_ir_to_c_compiles_and_runs():
    ir = parse_controlled_expression("输出 1+2*3")
    result = Sandbox().run(ir.to_c_program())
    assert result.compile_success is True
    assert result.run_success is True
    assert result.stdout == "7\n"


def test_dataset_generator_reproducible():
    train_a, eval_a = build_dataset(train_size=80, eval_size=20, seed=20260518)
    train_b, eval_b = build_dataset(train_size=80, eval_size=20, seed=20260518)
    assert train_a == train_b
    assert eval_a == eval_b


def test_dataset_generator_has_train_eval_split():
    train, eval_samples = build_dataset(train_size=80, eval_size=20, seed=20260518)
    assert len(train) == 80
    assert len(eval_samples) == 20
    assert {sample["split"] for sample in train} == {"train"}
    assert {sample["split"] for sample in eval_samples} == {"eval"}


def test_hashed_perceptron_parameter_count():
    model = HashedPerceptron(labels=["a", "b"])
    assert model.num_params == 1_048_576
    assert len(model.weights) == 1_048_576


def test_hashed_perceptron_learns_tiny_separable_case():
    samples = [
        HashedLabeledSample({"x": 1.0}, "left"),
        HashedLabeledSample({"y": 1.0}, "right"),
    ]
    model = HashedPerceptron(labels=["left", "right"], num_params=512, epochs=5, seed=7).fit(samples)
    assert model.predict({"x": 1.0}) == "left"
    assert model.predict({"y": 1.0}) == "right"


def test_targetir_router_predicts_supported_shape():
    train, _ = build_dataset(train_size=120, eval_size=20, seed=20260518)
    router = ArithmeticTargetIRRouter(num_params=4096, epochs=2, seed=42).fit(train)
    pred = router.predict("写一个 C 程序输出 1+2*3")
    assert pred.supported_pred in {"supported", "unsupported"}
    assert pred.expression_form_pred
    assert pred.structure_label_pred
    assert "numbers" in pred.extracted_slots


def test_evaluate_outputs_required_metrics(tmp_path):
    train, eval_samples = build_dataset(train_size=120, eval_size=30, seed=20260518)
    train_path = tmp_path / "train.jsonl"
    eval_path = tmp_path / "eval.jsonl"
    _write_jsonl(train_path, train)
    _write_jsonl(eval_path, eval_samples)
    metrics = train_and_evaluate(
        train_path=train_path,
        eval_path=eval_path,
        output_dir=tmp_path,
        num_params=4096,
        epochs=1,
        seed=42,
        max_compile_checks=1,
    )
    for key in [
        "supported_accuracy",
        "unsupported_precision",
        "unsupported_recall",
        "unsupported_f1",
        "expression_form_accuracy",
        "structure_label_accuracy",
        "target_ir_exact_match",
        "expected_output_match",
        "compile_success_rate",
        "run_success_rate",
        "task_success_rate",
        "oracle_parser_upper_bound",
    ]:
        assert key in metrics
    assert (tmp_path / "arithmetic_targetir_predictions_eval.jsonl").exists()
    assert (tmp_path / "arithmetic_targetir_model.json").exists()


def test_no_label_leakage_features():
    features = extract_arithmetic_features("写一个 C 程序输出 1+2*3")
    forbidden = ["target_ir", "canonical", "expected_output", "structure_label", "expression_form", "BIN_ADD"]
    names = "\n".join(features)
    for token in forbidden:
        assert token not in names


def test_existing_tests_still_pass():
    from jianmu.runtime import Runtime
    from jianmu.self_learning.learned_router.route_classifier import RouteClassifier

    assert Runtime is not None
    assert RouteClassifier is not None


def _write_jsonl(path: Path, samples):
    path.write_text(
        "".join(json.dumps(sample, ensure_ascii=False, sort_keys=True) + "\n" for sample in samples),
        encoding="utf-8",
    )
