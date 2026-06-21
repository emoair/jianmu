from jianmu.self_learning.darwinforge.redqueen_frontier_pressure_audit import audit_frontier_pressure


def test_redqueen_frontier_pressure_audit_tracks_shape_diversity(tmp_path):
    cycles = [{"execution": {"events": 1000, "actual_category_distribution": {"unsupported_boundary": 100}}}]
    result = audit_frontier_pressure(tmp_path, {"cycles": cycles})
    assert result["shape_diversity_increased"] is True
    assert result["frontier_pressure_audit_passed"] is True
