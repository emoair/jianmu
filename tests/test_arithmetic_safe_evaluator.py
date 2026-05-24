import pytest

from jianmu.self_learning.darwinforge.arithmetic_safe_evaluator import ArithmeticEvaluationError, evaluate_target_ir, safe_evaluate_expression, target_ir_to_expression


def test_safe_evaluator_exact_integer_division():
    value, ir = safe_evaluate_expression("8/2+3")
    assert value == 7
    assert ir["op"] == "add"


def test_safe_evaluator_rejects_division_by_zero():
    with pytest.raises(ArithmeticEvaluationError):
        safe_evaluate_expression("1/0")


def test_safe_evaluator_rejects_non_integer_division_as_supported():
    with pytest.raises(ArithmeticEvaluationError):
        safe_evaluate_expression("7/2")


def test_target_ir_roundtrip():
    value, ir = safe_evaluate_expression("(3+5)*2")
    assert evaluate_target_ir(ir) == value
    assert "*" in target_ir_to_expression(ir)
