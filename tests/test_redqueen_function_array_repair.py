from jianmu.self_learning.darwinforge.redqueen_function_array_repair import run_redqueen_assignments


def test_redqueen_function_array_repair_assignments(tmp_path):
    result = run_redqueen_assignments(tmp_path)
    ids = {row["assignment_id"] for row in result["assignments"]}
    assert "function_signature_repair_assignment" in ids
    assert "array_loop_bound_repair_assignment" in ids
    assert "function_array_interop_repair_assignment" in ids
    assert all(row["production_boundary_change"] is False for row in result["assignments"])
