from jianmu.self_learning.darwinforge.turing_frontier_redqueen_repair import generate_redqueen_repair_assignments


def test_redqueen_frontier_repair_assignments(tmp_path):
    result = generate_redqueen_repair_assignments(tmp_path)
    ids = {row["assignment_id"] for row in result["assignments"]}
    assert "loop_variant_repair_assignment" in ids
    assert "recursive_base_case_repair_assignment" in ids
    assert result["redqueen_repair_assignments_completed"] is True
    assert all(row["safety_contract"]["production_boundary_change"] is False for row in result["assignments"])
