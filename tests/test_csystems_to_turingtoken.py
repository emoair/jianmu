from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row


def test_csystems_to_turingtoken():
    row = build_csystems_row(2)
    assert row["expected_token_type"] == "turingtoken"
    assert row["target_token"] is not None
