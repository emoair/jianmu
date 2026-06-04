from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_linguaforge_assignments import redqueen_assignments


def test_redqueen_linguaforge_assignments_shadow_only() -> None:
    assignments = redqueen_assignments()
    assert assignments["nl_loop_boundary_assignment"]["enabled"] is True
    assert assignments["bounded_regression_guard_assignment"]["real_promotion"] is False

