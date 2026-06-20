from jianmu.self_learning.darwinforge.redqueen_governance_drift_audit import audit_governance_drift


def test_redqueen_governance_drift_audit_blocks_real_promotion(tmp_path):
    result = audit_governance_drift(tmp_path, {"default_profile_unchanged": True, "real_promotion_enabled": True})
    assert result["governance_drift_detected"] is True
    assert result["governance_drift_audit_passed"] is False


def test_redqueen_governance_drift_audit_blocks_template_bypass(tmp_path):
    result = audit_governance_drift(tmp_path, {"default_profile_unchanged": True, "direct_template_path_detected": True})
    assert result["direct_template_path_detected"] is True
    assert result["governance_drift_audit_passed"] is False
