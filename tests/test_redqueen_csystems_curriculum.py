from jianmu.self_learning.darwinforge.redqueen_csystems_curriculum import redqueen_curriculum


def test_redqueen_csystems_curriculum_assignments():
    result = redqueen_curriculum()
    assert "pointer_dereference_assignment" in result
    assert "algorithm_regression_guard_assignment" in result
    assert all(item["safety_contract"] for item in result.values())
