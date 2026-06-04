from __future__ import annotations

from jianmu.self_learning.darwinforge.algorithm_compiler_validation import full_compile_validation, syntax_frontend_check
from jianmu.self_learning.darwinforge.forgecorpus_algorithm_schema import build_algorithm_row


def test_algorithm_compiler_validation_uses_full_compile() -> None:
    rows = [{"project_source": build_algorithm_row("pilot", i)["algorithm_source"], "expected_output": build_algorithm_row("pilot", i)["expected_output"], "id": str(i), "support_status": "current_supported"} for i in range(20) if build_algorithm_row("pilot", i)["support_status"] == "current_supported"]
    result = full_compile_validation(rows, target=5)
    assert result["compiler_validation_completed"] is True
    assert result["wrong_stdout_count"] == 0


def test_syntax_filter_not_correctness_evidence() -> None:
    rows = [{"project_source": build_algorithm_row("pilot", i)["algorithm_source"], "support_status": "current_supported"} for i in range(20) if build_algorithm_row("pilot", i)["support_status"] == "current_supported"]
    result = syntax_frontend_check(rows, target=5)
    assert result["syntax_filter_used_as_correctness_evidence"] is False

