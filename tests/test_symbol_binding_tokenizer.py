from jianmu.self_learning.darwinforge.symbol_binding_longhaul_core import build_symbol_binding_row


def test_symbol_binding_tokenizer_projecttoken():
    row = build_symbol_binding_row(0)
    assert row["target_token"]["token_type"] == "project_standardtoken"

