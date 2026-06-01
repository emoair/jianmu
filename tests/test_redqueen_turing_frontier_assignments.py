from jianmu.self_learning.darwinforge.redqueen_turing_frontier_assignments import redqueen_frontier_assignments


def test_redqueen_turing_frontier_assignments(tmp_path):
    result = redqueen_frontier_assignments(tmp_path)
    names = {row["assignment"] for row in result["assignments"]}
    assert "unbounded_while_terminating_assignment" in names
    assert "recursion_missing_base_case_assignment" in names
    assert result["assignment_count"] == 12
