from __future__ import annotations

import random

from jianmu.self_learning.darwinforge.turing_substrate_grammar import SUPPORTED_STAGES, generate_supported_program, render_program
from jianmu.self_learning.darwinforge.turing_substrate_safe_interpreter import evaluate_program


def test_turing_substrate_grammar_generates_supported_programs() -> None:
    rng = random.Random(52)
    for index, stage in enumerate(SUPPORTED_STAGES):
        ir = generate_supported_program(stage, rng, index)
        assert ir["op"] == "Program"
        assert evaluate_program(ir).endswith("\n")
        assert render_program(ir)
