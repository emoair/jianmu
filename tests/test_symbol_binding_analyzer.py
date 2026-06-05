from jianmu.self_learning.darwinforge.symbol_binding_analyzer import binding_metrics
from jianmu.self_learning.darwinforge.symbol_binding_longhaul_core import build_symbol_binding_row


def test_symbol_binding_analyzer_metrics():
    metrics = binding_metrics([build_symbol_binding_row(i) for i in range(100)])
    assert metrics["identifier_binding_success_rate"] >= 0.92
    assert metrics["multifile_symbol_consistency_rate"] >= 0.86

