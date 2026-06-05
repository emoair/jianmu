from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row, fileio_sandbox_audit


def test_csystems_fileio_sandbox_audit():
    result = fileio_sandbox_audit([build_csystems_row(40)])
    assert result["fileio_contract_passed"] is True
