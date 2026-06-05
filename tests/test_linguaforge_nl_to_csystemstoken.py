from jianmu.self_learning.darwinforge.linguaforge_nl_alpha_core import build_row


def test_nl_to_csystemstoken():
    rows = [build_row(i, 188) for i in range(300)]
    token_rows = [r for r in rows if r["expected_token_type"] == "csystemstoken" and r["support_status"] == "current_supported"]
    assert token_rows
    assert token_rows[0]["target_token"]["token_type"] == "csystemstoken"
