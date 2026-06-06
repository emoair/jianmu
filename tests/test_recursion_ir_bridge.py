from jianmu.extended_ir import RecursiveFunctionProgram
from jianmu.self_learning.darwinforge.recursion_ir_bridge import build_factorial_program


def test_recursion_ir_bridge_reuses_turing_frontier_contract():
    program = build_factorial_program(5)
    assert isinstance(program, RecursiveFunctionProgram)
    assert program.recursion_mode == "bounded_structural_recursion_validation"
    assert program.production_recursion_support is False
    assert program.expected_stdout == "120\n"

