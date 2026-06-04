from __future__ import annotations

from jianmu.self_learning.darwinforge.project_compiler_validation import full_compile_validation, syntax_frontend_check
from jianmu.self_learning.darwinforge.project_dataset_builder import build_project_row


def test_project_compiler_validation_uses_full_compile_path() -> None:
    rows = [build_project_row("pilot", i) for i in range(50)]
    metrics = full_compile_validation(rows, target=5)
    assert metrics["compiler_validation_completed"] is True
    assert metrics["wrong_stdout_count"] == 0


def test_syntax_frontend_not_counted_as_correctness() -> None:
    rows = [build_project_row("pilot", i) for i in range(50)]
    metrics = syntax_frontend_check(rows, target=5)
    assert metrics["syntax_filter_used_as_correctness_evidence"] is False

