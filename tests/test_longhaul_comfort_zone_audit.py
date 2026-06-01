from jianmu.self_learning.darwinforge.longhaul_comfort_zone_audit import (
    run_longhaul_comfort_zone_audit,
    run_longhaul_generalization_audit,
)


def test_longhaul_comfort_zone_audit(tmp_path):
    audit = run_longhaul_comfort_zone_audit(tmp_path)
    assert audit["comfort_zone_collapse_detected"] is False
    assert audit["trunk_solved_program_ratio"] <= 0.10


def test_longhaul_generalization_audit(tmp_path):
    audit = run_longhaul_generalization_audit(tmp_path)
    assert audit["generalization_audit_passed"] is True
    assert "template_family_holdout" in audit["holdout_groups"]
