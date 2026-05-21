from jianmu.self_learning.darwinforge.freebeam_rejection_diagnostics import diagnose_freebeam_rejection


def test_freebeam_rejection_diagnostics_confirms_signal_only_when_safe():
    metrics = {
        "hard_ood_rejection_rate": 0.9,
        "true_false_accept_trap_rejection_rate": 0.9,
        "overall_ood_false_accept_rate": 0.1,
        "current_supported_retention_rate": 0.99,
    }
    result = diagnose_freebeam_rejection(metrics, [], {"no_label_inference_passed": True}, {"real_promotion_enabled": False, "hardcoded_rejection_gate_added": False})
    assert result["freebeam_emergent_rejection_signal_confirmed"] is True


def test_freebeam_rejection_diagnostics_detects_over_rejection():
    result = diagnose_freebeam_rejection({"current_supported_retention_rate": 0.9}, [], {"no_label_inference_passed": True})
    assert result["over_rejection_detected"] is True


def test_freebeam_rejection_diagnostics_detects_failed_generalization():
    result = diagnose_freebeam_rejection({"current_supported_retention_rate": 1.0, "overall_ood_false_accept_rate": 0.8}, [], {"no_label_inference_passed": True})
    assert result["boundary_probe_did_not_generalize"] is True


def test_mainline_conclusion_ledger_exists():
    import pathlib

    assert pathlib.Path("records/v0_8_7/mainline_conclusion.md").exists()
