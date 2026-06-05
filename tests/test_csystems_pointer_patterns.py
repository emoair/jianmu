from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row


def test_pointer_patterns_basic():
    row = build_csystems_row(0)
    assert row["feature_family"] == "pointer_frontier"
    assert row["system_features"]["has_pointer"] is True
    assert "&" in row["combined_source"] or "*" in row["combined_source"]
