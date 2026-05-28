from __future__ import annotations

from jianmu.self_learning.darwinforge.turing_frontier_grammar import language_features_for, simple_supported_ir


def test_turing_frontier_unbounded_loop_not_supported() -> None:
    features = language_features_for("unsupported_unbounded_loop", "unsupported_unbounded_loop")
    assert features["has_unbounded_loop"] is True
    assert features["has_recursion"] is False


def test_turing_frontier_recursion_array_function_not_supported() -> None:
    assert language_features_for("future_recursion_candidate", "future_recursion")["has_recursion"] is True
    assert language_features_for("future_array_candidate", "future_array")["has_array"] is True
    assert language_features_for("future_function_candidate", "future_function")["has_function"] is True


def test_supported_ir_is_json_ast_not_c_source() -> None:
    ir = simple_supported_ir(3)
    assert ir["op"] == "Program"
    assert "#include" not in str(ir)

