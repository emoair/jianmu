from pathlib import Path

from jianmu.self_learning.darwinforge.symbol_binding_compiler_validation import compiler_validation
from jianmu.self_learning.darwinforge.symbol_binding_longhaul_core import build_symbol_binding_row


def test_symbol_binding_compiler_validation_uses_full_compile(tmp_path):
    rows = [build_symbol_binding_row(i) for i in range(16)]
    metrics = compiler_validation(rows, Path(tmp_path), 8)
    assert metrics["full_compile_invocation_count"] == 8
    assert metrics["compiler_verified_correctness_rate"] == 1.0

