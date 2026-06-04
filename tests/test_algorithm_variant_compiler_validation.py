from pathlib import Path

from jianmu.self_learning.darwinforge.algorithm_variant_generator import build_variant_row
from jianmu.self_learning.darwinforge.projectcartographer_schema import full_compile_validation, syntax_frontend_check


def test_variant_compiler_validation_uses_full_compile(tmp_path):
    rows = []
    for i in range(40):
        row = build_variant_row("pilot", i)
        if row["support_status"] == "current_supported":
            rows.append({"project_source": row["algorithm_source"], "expected_output": row["expected_output"], "id": row["id"], "support_status": row["support_status"]})
    result = full_compile_validation(rows[:5], 5, Path(tmp_path))
    assert result["real_compiler_invocation_count"] == 5
    assert result["compiler_verified_correctness_rate"] == 1.0


def test_syntax_filter_not_correctness_evidence():
    row = build_variant_row("pilot", 0)
    result = syntax_frontend_check([{"project_source": row["algorithm_source"], "support_status": row["support_status"]}], 1)
    assert result["syntax_filter_used_as_correctness_evidence"] is False
