from __future__ import annotations

from jianmu.self_learning.darwinforge.bounded_substrate_boundary_eval import REQUIRED_BOUNDARY_CATEGORIES, evaluate_boundary


def test_bounded_substrate_boundary_eval_has_required_categories() -> None:
    result = evaluate_boundary([])
    assert list(result["by_category"].keys()) == REQUIRED_BOUNDARY_CATEGORIES


def test_unbounded_loop_false_accept_metric() -> None:
    assert evaluate_boundary([])["unbounded_loop_false_accept_rate"] == 0.0


def test_recursion_false_accept_metric() -> None:
    assert evaluate_boundary([])["recursion_false_accept_rate"] == 0.0


def test_pointer_array_function_false_accept_metrics() -> None:
    result = evaluate_boundary([])
    assert result["pointer_false_accept_rate"] == 0.0
    assert result["array_false_accept_rate"] == 0.0
    assert result["function_false_accept_rate"] == 0.0
