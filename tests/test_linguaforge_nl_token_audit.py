from jianmu.self_learning.darwinforge.linguaforge_nl_alpha_core import build_row
from jianmu.self_learning.darwinforge.linguaforge_nl_token_audit import token_audit


def test_nl_token_audit_blocks_raw_c_source():
    metrics = token_audit([build_row(i, 188) for i in range(30)])
    assert metrics["nl_contains_raw_c_source_count"] == 0
    assert metrics["token_contains_raw_c_source_count"] == 0


def test_nl_token_audit_blocks_raw_target_ir_json():
    metrics = token_audit([build_row(i, 188) for i in range(30)])
    assert metrics["nl_contains_raw_target_ir_json_count"] == 0
    assert metrics["token_contains_raw_target_ir_json_count"] == 0


def test_unsupported_nl_has_no_target_ir_or_expected_output():
    rows = [build_row(i, 188) for i in range(300)]
    unsupported = [r for r in rows if r["support_status"] in {"unsupported", "review"}]
    assert unsupported
    assert all(r["target_ir"] is None and r["expected_output"] is None for r in unsupported)


def test_ambiguous_nl_does_not_fabricate_expected_output():
    rows = [build_row(i, 188) for i in range(300)]
    review = [r for r in rows if r["support_status"] == "review"]
    assert review
    assert all(r["expected_output"] is None for r in review)
