from jianmu.self_learning.darwinforge.mirror_negative_boundary_audit import run_mirror_negative_boundary_audit


def test_mirror_negative_boundary_blocks_no_opt_in(tmp_path) -> None:
    result = run_mirror_negative_boundary_audit(tmp_path)
    assert result["no_opt_in_blocked"] is True
    assert result["mirror_negative_boundary_audit_passed"] is True

