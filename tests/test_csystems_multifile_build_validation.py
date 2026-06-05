from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row, multifile_build_validation


def test_multifile_build_validation_uses_real_link(tmp_path):
    rows = [build_csystems_row(i) for i in range(60, 80)]
    result = multifile_build_validation(rows, tmp_path, target=2)
    assert result["real_multifile_link_invocation_count"] == 2
    assert result["multifile_compile_link_success_rate"] == 1.0
