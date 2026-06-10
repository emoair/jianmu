from jianmu.self_learning.darwinforge.production_bridge_interface_review import run_interface_landing_review


def test_interface_landing_review_checks_atomic_policies(tmp_path):
    result = run_interface_landing_review(tmp_path)
    assert result["atomic_policy_interfaces_valid"] is True


def test_interface_landing_review_checks_extended_ir(tmp_path):
    result = run_interface_landing_review(tmp_path)
    assert result["extended_ir_interfaces_valid"] is True


def test_interface_landing_review_checks_extended_emitter(tmp_path):
    result = run_interface_landing_review(tmp_path)
    assert result["extended_emitter_interfaces_valid"] is True
    assert result["template_bypass_detected"] is False

