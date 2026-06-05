from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row
from jianmu.self_learning.darwinforge.csystems_fileio_sandbox_audit import fileio_sandbox_audit


def test_fileio_patterns_sandbox_only():
    row = build_csystems_row(40)
    assert row["feature_family"] == "fileio_frontier"
    assert row["fileio_contract"]["sandbox_temp_path_only"] is True
    assert ".." not in row["combined_source"]


def test_fileio_blocks_absolute_and_parent_paths():
    row = build_csystems_row(40)
    assert row["fileio_contract"]["absolute_path_used"] is False
    assert row["fileio_contract"]["parent_path_used"] is False


def test_fileio_sandbox_blocks_unsafe_path():
    result = fileio_sandbox_audit([build_csystems_row(40)])
    assert result["unsafe_path_blocked_count"] >= 1
    assert result["sandbox_escape_attempt_count"] == 0
