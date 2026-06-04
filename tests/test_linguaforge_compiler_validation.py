from __future__ import annotations

from jianmu.self_learning.darwinforge.linguaforge_compiler_validation import compiler_validation
from jianmu.self_learning.darwinforge.linguaforge_nl_schema import build_linguaforge_row


def test_linguaforge_compiler_validation_reports_real_cl_path() -> None:
    rows = [build_linguaforge_row("pilot", i) for i in range(40)]
    metrics = compiler_validation(rows, target=10)
    assert metrics["compiler_validation_completed"] is True
    assert metrics["future_domain_compiled_count"] == 0
    assert metrics["wrong_stdout_count"] == 0

