from jianmu.self_learning.darwinforge.emergent_rejection_diagnostics import diagnose_emergent_rejection


def test_emergent_rejection_requires_supported_retention():
    before = {"current_supported_retention_rate": 1.0, "hard_ood_rejection_rate": 0.1, "true_false_accept_trap_rejection_rate": 0.1, "overall_ood_false_accept_rate": 0.9}
    after = {"current_supported_retention_rate": 0.99, "hard_ood_rejection_rate": 0.8, "true_false_accept_trap_rejection_rate": 0.8, "overall_ood_false_accept_rate": 0.2}
    diag = diagnose_emergent_rejection(before, after, {"real_promotion_enabled": False, "hardcoded_rejection_rules_added": False})
    assert diag["emergent_rejection_signal_confirmed"] is True


def test_emergent_rejection_detects_over_rejection():
    before = {"current_supported_retention_rate": 1.0, "hard_ood_rejection_rate": 0.1, "true_false_accept_trap_rejection_rate": 0.1, "overall_ood_false_accept_rate": 0.9}
    after = {"current_supported_retention_rate": 0.5, "hard_ood_rejection_rate": 0.8, "true_false_accept_trap_rejection_rate": 0.8, "overall_ood_false_accept_rate": 0.2}
    diag = diagnose_emergent_rejection(before, after, {"real_promotion_enabled": False, "hardcoded_rejection_rules_added": False})
    assert diag["over_rejection_detected"] is True
    assert diag["emergent_rejection_signal_confirmed"] is False
