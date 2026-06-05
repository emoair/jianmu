from jianmu.self_learning.darwinforge.symbol_binding_longhaul_core import build_symbol_binding_row
from jianmu.self_learning.darwinforge.symbol_binding_roundtrip_eval import roundtrip_metrics


def test_symbol_binding_roundtrip_eval():
    metrics = roundtrip_metrics([build_symbol_binding_row(i) for i in range(100)])
    assert metrics["token_to_ir_success_rate"] >= 0.94

