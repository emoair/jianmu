from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row


def test_csystems_to_mirrortoken():
    row = build_csystems_row(1)
    assert row["expected_token_type"] == "mirrortoken"
    assert row["target_token"] is not None
