from jianmu.self_learning.darwinforge.algorithm_sample_accounting import sample_accounting
from jianmu.self_learning.darwinforge.algorithm_variant_generator import build_variant_row


def test_sample_accounting_separates_skeletons_and_variants():
    rows = [build_variant_row("pilot", i) for i in range(100)]
    result = sample_accounting(rows)
    assert result["semantic_skeleton_count"] <= result["expanded_variant_count"]
    assert result["deduplicated_surface_shape_count"] > 1
    assert result["train_sample_count"] > 0
