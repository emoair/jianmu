from jianmu.self_learning.darwinforge.real_compiler_accounting_audit import accounting_audit
from jianmu.self_learning.darwinforge.symbol_binding_longhaul_core import build_symbol_binding_row


def test_real_compiler_accounting_detects_cached_as_new():
    rows = [build_symbol_binding_row(i) for i in range(20)]
    compiler = {"full_compile_invocation_count": 10, "backend_claim_safe": True, "wrong_stdout_count": 0}
    metrics = accounting_audit(compiler, rows)
    assert metrics["cached_result_used_as_new_count"] == 0


def test_real_compiler_accounting_detects_stubbed_validation():
    rows = [build_symbol_binding_row(i) for i in range(20)]
    compiler = {"full_compile_invocation_count": 10, "backend_claim_safe": True, "wrong_stdout_count": 0}
    metrics = accounting_audit(compiler, rows)
    assert metrics["stubbed_validation_detected"] is False

