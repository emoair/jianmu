from jianmu.self_learning.darwinforge.symbiote_generalization_audit import run_generalization_audit


def test_generalization_audit_holdout_groups(tmp_path):
    result = run_generalization_audit(tmp_path)
    assert result["generalization_audit_passed"] is True
    assert "template_family_holdout" in result["holdout_groups"]
