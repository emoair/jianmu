from jianmu.self_learning.darwinforge.arithmetic_boundary_eval import REQUIRED_BOUNDARY_CATEGORIES, evaluate_arithmetic_boundary


def test_arithmetic_boundary_eval_has_required_categories():
    rows = [{"id": cat, "category": cat, "division_kind": "none"} for cat in REQUIRED_BOUNDARY_CATEGORIES]
    result = evaluate_arithmetic_boundary(rows)
    assert {row["category"] for row in result["by_category"]} == set(REQUIRED_BOUNDARY_CATEGORIES)


def test_division_by_zero_false_accept_metric():
    result = evaluate_arithmetic_boundary([{"id": "z", "category": "unsupported_arithmetic_boundary", "division_kind": "division_by_zero"}])
    assert result["division_by_zero_false_accept_rate"] == 0.0


def test_non_integer_division_false_accept_metric():
    result = evaluate_arithmetic_boundary([{"id": "n", "category": "near_ood_arithmetic", "division_kind": "non_integer"}])
    assert result["non_integer_division_false_accept_rate"] == 0.0
