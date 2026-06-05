from jianmu.self_learning.darwinforge.symbol_binding_longhaul_core import build_symbol_binding_row
from jianmu.self_learning.darwinforge.symbol_binding_token_audit import token_metrics


def test_symbol_binding_token_audit_no_raw_c_source():
    metrics = token_metrics([build_symbol_binding_row(i) for i in range(100)])
    assert metrics["token_contains_c_source_count"] == 0


def test_symbol_binding_token_audit_no_target_ir_json():
    metrics = token_metrics([build_symbol_binding_row(i) for i in range(100)])
    assert metrics["token_contains_raw_target_ir_json_count"] == 0

