from jianmu.self_learning.darwinforge.algorithm_variant_heldout_taxonomy import heldout_failure_taxonomy


def test_heldout_variant_failure_taxonomy():
    result = heldout_failure_taxonomy()
    assert result["taxonomy_completed"] is True
    assert "boundary_value_off_by_one" in result["failure_category_distribution"]
