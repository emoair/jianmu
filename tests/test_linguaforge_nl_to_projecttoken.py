from jianmu.self_learning.darwinforge.linguaforge_nl_alpha_core import build_row


def test_nl_to_projecttoken_no_direct_c_generation():
    row = build_row(105, 188)
    if row["expected_token_type"] == "projecttoken" and row["support_status"] == "current_supported":
        assert row["target_token"]["token_type"] == "projecttoken"
    assert row["leakage_guard"]["nl_direct_c_generation"] is False
    assert row["leakage_guard"]["nl_bypassed_token_layer"] is False
