from jianmu.self_learning.darwinforge.policy_interface_landing_audit import audit_policy_interface_landing


def test_policy_interface_landing_audit():
    result = audit_policy_interface_landing()
    assert result["atomic_policy_interfaces_valid"] is True
    assert result["unknown_policy_rejected"] is True

