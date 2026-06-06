from jianmu.extended_emitter_c import ExtendedEmitterC
from jianmu.self_learning.darwinforge.function_array_ir_bridge import build_array_program, build_function_array_program, build_function_program
from jianmu.self_learning.darwinforge.recursion_ir_bridge import build_factorial_program


def test_extended_emitter_emits_function_program():
    source = ExtendedEmitterC().emit(build_function_program(7))
    assert "static int calc(int x)" in source
    assert "printf" in source
    assert "calc(6)" in source


def test_extended_emitter_emits_array_program():
    source = ExtendedEmitterC().emit(build_array_program(7))
    assert "int a[4]" in source
    assert "for (int i = 0; i < 4; i++)" in source
    assert "a[i]" in source


def test_extended_emitter_emits_function_array_program():
    source = ExtendedEmitterC().emit(build_function_array_program(7))
    assert "static int sum3(int a[])" in source
    assert "sum3(a)" in source
    assert "a[i]" in source


def test_extended_emitter_emits_structured_recursion_program():
    source = ExtendedEmitterC().emit(build_factorial_program(4))
    assert "static int fact(int n)" in source
    assert "fact((n - 1))" in source
    assert "fact(4)" in source

