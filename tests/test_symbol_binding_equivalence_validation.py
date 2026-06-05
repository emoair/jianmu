from jianmu.self_learning.darwinforge.symbol_binding_equivalence_validation import equivalence_validation
from jianmu.self_learning.darwinforge.symbol_binding_longhaul_core import build_symbol_binding_row


def test_symbol_binding_equivalence_validation():
    metrics = equivalence_validation([build_symbol_binding_row(i) for i in range(100)])
    assert metrics["mutation_equivalence_validation_completed"] is True
    assert metrics["output_equivalence_success_rate"] >= 0.90

