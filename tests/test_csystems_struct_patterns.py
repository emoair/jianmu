from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row


def test_struct_patterns_basic():
    row = build_csystems_row(62)
    assert row["feature_family"] == "struct_frontier"
    assert row["system_features"]["has_struct"] is True
    assert "struct" in row["combined_source"]
