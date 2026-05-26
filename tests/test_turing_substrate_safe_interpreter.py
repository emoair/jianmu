from __future__ import annotations

import pytest

from jianmu.self_learning.darwinforge.turing_substrate_grammar import generate_supported_program
from jianmu.self_learning.darwinforge.turing_substrate_safe_interpreter import TuringSubstrateError, evaluate_program


def test_turing_substrate_safe_interpreter_matches_simple_program() -> None:
    program = {
        "op": "Program",
        "body": [
            {"op": "VarDecl", "name": "x", "value": {"op": "Int", "value": 3}},
            {"op": "Assign", "name": "x", "value": {"op": "Add", "args": [{"op": "Var", "name": "x"}, {"op": "Int", "value": 2}]}},
            {"op": "Print", "value": {"op": "Var", "name": "x"}},
        ],
    }
    assert evaluate_program(program) == "5\n"


def test_turing_substrate_rejects_unbounded_loop_as_supported() -> None:
    bad = {"op": "Program", "body": [{"op": "ForBounded", "var": "i", "bound": 1000, "body": []}]}
    with pytest.raises(TuringSubstrateError):
        evaluate_program(bad)


def test_turing_substrate_generated_loop_runs() -> None:
    assert evaluate_program(generate_supported_program("bounded_for_loop", __import__("random").Random(1))).endswith("\n")
