from jianmu.self_learning.darwinforge.symbiote_comfort_zone_audit import run_comfort_zone_audit


def test_comfort_zone_audit_detects_trunk_solved_overuse(tmp_path):
    result = run_comfort_zone_audit(tmp_path, trunk_solved_program_ratio=0.15)
    assert result["comfort_zone_collapse_detected"] is True
    assert result["comfort_zone_audit_passed"] is False
