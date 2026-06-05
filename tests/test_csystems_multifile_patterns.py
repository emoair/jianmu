from jianmu.self_learning.darwinforge.csystems_frontier_core import build_csystems_row


def test_multifile_patterns_header_source_match():
    row = build_csystems_row(56)
    assert row["feature_family"] == "multifile_frontier"
    assert row["project_layout"] == "multi_file"
    assert "algo.h" in row["files"]
    assert row["build_contract"]["header_declaration_match"] is True
