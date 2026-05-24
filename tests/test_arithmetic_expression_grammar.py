from random import Random

from jianmu.self_learning.darwinforge.arithmetic_expression_grammar import SUPPORTED_STAGES, generate_supported_expression
from jianmu.self_learning.darwinforge.arithmetic_safe_evaluator import safe_evaluate_expression


def test_arithmetic_grammar_generates_valid_supported_expressions():
    rng = Random(7)
    for stage in SUPPORTED_STAGES:
        expr = generate_supported_expression(stage, rng)
        value, ir = safe_evaluate_expression(expr)
        assert isinstance(value, int)
        assert ir is not None
