from __future__ import annotations

from jianmu.self_learning.darwinforge.forgecorpus_algorithm_schema import ClassicCAlgorithmFamilyConfig


def test_forgecorpus_algorithm_family_config() -> None:
    families = ClassicCAlgorithmFamilyConfig.families()
    assert "bubble_sort" in families["sorting"]
    assert "binary_search" in families["search"]
    assert "matrix_multiply_small" in families["matrix"]
    assert "counter_machine_decjz" in families["turing_witness"]

