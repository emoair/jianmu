from jianmu.self_learning.darwinforge.algorithm_variant_generator import build_variant_row


def test_variant_tokenizer_no_raw_c_source():
    row = build_variant_row("pilot", 0)
    assert row["leakage_guard"]["token_contains_c_source"] is False


def test_variant_tokenizer_no_target_ir_json():
    row = build_variant_row("pilot", 0)
    assert row["leakage_guard"]["token_contains_raw_target_ir_json"] is False
