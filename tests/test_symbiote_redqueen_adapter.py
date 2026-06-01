from jianmu.self_learning.darwinforge.symbiote_redqueen_adapter import build_symbiote_redqueen_assignments


def test_redqueen_symbiote_assignments(tmp_path):
    result = build_symbiote_redqueen_assignments(tmp_path)
    assert result["symbiote_redqueen_assignments_completed"] is True
    assert result["capability_boundary_changed"] is False
    assert result["comfort_zone_breaker_assignments"]
