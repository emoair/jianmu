from jianmu.self_learning.darwinforge.turing_frontier_failure_taxonomy import FAILURE_TYPES, analyze_failure_taxonomy


def test_failure_taxonomy_outputs_required_categories(tmp_path):
    result = analyze_failure_taxonomy("records/v0_9_26", tmp_path)
    assert result["taxonomy_completed"] is True
    for category in FAILURE_TYPES:
        assert category in result["failure_distribution"]
    assert result["dominant_failure_type"] == "loop_variant_missing"
