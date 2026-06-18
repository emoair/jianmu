from jianmu.self_learning.darwinforge.unsupported_boundary_matrix import build_unsupported_boundary_matrix


def test_unsupported_boundary_matrix_blocks_unsafe_cases(tmp_path):
    result = build_unsupported_boundary_matrix(tmp_path)
    rows = {row["unsupported_case"]: row for row in result["unsupported_cases"]}
    assert rows["malloc/free request"]["compile_invoked"] is False
    assert rows["production promotion request"]["real_promotion_enabled"] is False
    assert rows["unknown policy"]["expected_behavior"] == "reject"
