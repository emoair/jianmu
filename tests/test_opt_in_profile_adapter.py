from jianmu.self_learning.darwinforge.opt_in_profile_adapter import audit_opt_in_adapter


def test_opt_in_profile_adapter_reuses_v1_0_6_adapter(tmp_path):
    result = audit_opt_in_adapter(tmp_path)
    assert result["adapter_reuses_v1_0_6_dry_run_adapter"] is True


def test_opt_in_profile_adapter_reuses_atomic_policy_bridge(tmp_path):
    result = audit_opt_in_adapter(tmp_path)
    assert result["adapter_reuses_atomic_policy_bridge"] is True
    assert result["direct_template_path_detected"] is False
