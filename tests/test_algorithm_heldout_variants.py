from __future__ import annotations

from jianmu.self_learning.darwinforge.algorithm_heldout_variants import heldout_variants


def test_heldout_algorithm_variants() -> None:
    result = heldout_variants()
    assert result["variant_generalization_passed"] is True
    assert result["heldout_algorithm_variant_success_rate"] >= 0.85

