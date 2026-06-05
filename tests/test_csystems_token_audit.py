from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row, token_metrics


def test_csystems_token_audit_no_raw_c_source():
    rows = [build_csystems_row(i) for i in range(100)]
    assert token_metrics(rows)["token_contains_c_source_count"] == 0


def test_csystems_token_audit_no_target_ir_json():
    rows = [build_csystems_row(i) for i in range(100)]
    assert token_metrics(rows)["token_contains_raw_target_ir_json_count"] == 0
