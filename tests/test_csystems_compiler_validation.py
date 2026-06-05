from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row, compiler_validation
from jianmu.self_learning.darwinforge.projectcartographer_schema import syntax_frontend_check


def test_csystems_compiler_validation_uses_full_compile(tmp_path):
    rows = [build_csystems_row(i) for i in range(80)]
    result = compiler_validation(rows, tmp_path, 5)
    assert result["real_compiler_invocation_count"] == 5
    assert result["compiler_verified_correctness_rate"] == 1.0


def test_syntax_filter_not_correctness_evidence():
    row = build_csystems_row(0)
    result = syntax_frontend_check([{"project_source": row["combined_source"], "support_status": row["support_status"]}], 1)
    assert result["syntax_filter_used_as_correctness_evidence"] is False
