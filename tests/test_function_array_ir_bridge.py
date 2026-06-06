from jianmu.extended_ir import ArrayProgram, FunctionArrayProgram, FunctionCallProgram
from jianmu.self_learning.darwinforge.forgefrontier_function_array_generator import make_forgefrontier_sample
from jianmu.self_learning.darwinforge.function_array_ir_bridge import forgefrontier_row_to_extended_ir


def test_function_array_ir_bridge_reuses_forgefrontier_logic():
    function_row = make_forgefrontier_sample(0, "pilot")
    array_row = make_forgefrontier_sample(20, "pilot")
    combo_row = make_forgefrontier_sample(70, "pilot")
    assert isinstance(forgefrontier_row_to_extended_ir(function_row), FunctionCallProgram)
    assert isinstance(forgefrontier_row_to_extended_ir(array_row), ArrayProgram)
    assert isinstance(forgefrontier_row_to_extended_ir(combo_row), FunctionArrayProgram)

