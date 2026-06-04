from __future__ import annotations

from jianmu.self_learning.darwinforge.redqueen_algorithm_curriculum import redqueen_curriculum


def test_redqueen_algorithm_curriculum_assignments() -> None:
    result = redqueen_curriculum()
    assert "quicksort_partition_assignment" in result
    assert result["bounded_regression_guard_assignment"]["safety_contract"] == "Boundary-as-Data-Contract"

