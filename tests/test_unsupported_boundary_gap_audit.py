import json

from jianmu.self_learning.darwinforge.unsupported_boundary_gap_audit import REQUIRED_BOUNDARIES, audit_unsupported_boundary_gap


def test_unsupported_boundary_gap_audit_requires_dangerous_boundaries(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    rows = [{"unsupported_case": case, "compile_invoked": False} for case in REQUIRED_BOUNDARIES if case != "malloc/free request"]
    (source / "unsupported_boundary_matrix.json").write_text(json.dumps({"unsupported_cases": rows}), encoding="utf-8")
    result = audit_unsupported_boundary_gap(source, tmp_path / "out")
    assert result["dangerous_boundary_missing"] is True
    assert "malloc/free request" in result["missing_boundaries"]
