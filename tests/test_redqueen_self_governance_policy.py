from jianmu.self_learning.darwinforge.redqueen_self_governance_policy import build_self_governance_policy


def test_redqueen_self_governance_policy_forbids_promotion(tmp_path):
    result = build_self_governance_policy(tmp_path)
    assert "enable_real_promotion" in result["forbidden_actions"]
    assert result["production_promotion_forbidden"] is True


def test_redqueen_self_governance_policy_forbids_default_profile_modification(tmp_path):
    result = build_self_governance_policy(tmp_path)
    assert "modify_default_profile" in result["forbidden_actions"]
    assert result["default_profile_modification_forbidden"] is True
