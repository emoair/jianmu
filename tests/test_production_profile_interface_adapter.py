from jianmu.self_learning.darwinforge.production_profile_interface_adapter import audit_interface_adapter


def test_interface_adapter_reuses_atomic_policy_bridge(tmp_path):
    result = audit_interface_adapter(tmp_path)
    assert result["adapter_reuses_atomic_policy_bridge"] is True
    assert result["adapter_interface_valid"] is True


def test_interface_adapter_reuses_extended_ir_and_emitter(tmp_path):
    result = audit_interface_adapter(tmp_path)
    assert result["adapter_reuses_extended_ir"] is True
    assert result["adapter_reuses_extended_emitter"] is True
    assert result["direct_template_path_detected"] is False
