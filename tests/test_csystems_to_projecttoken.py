from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row


def test_csystems_to_projecttoken():
    row = build_csystems_row(0)
    assert row["target_token"] is not None
    assert row["expected_token_type"] == "project_standardtoken"
