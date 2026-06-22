from jianmu.self_learning.darwinforge.redqueen_perturbation_recovery_audit import audit_perturbation_recovery


def test_redqueen_perturbation_recovery_audit_requires_final_clean_cycle():
    cycles = [{"cycle_index": i, "signal_schedule": [], "plan": {"active_review_allocations": {"unsupported_boundary": 1.0}}, "execution": {"cycle_completed": True, "compiler_verified_correctness_rate": 1.0, "wrong_stdout_count": 0}} for i in range(8)]
    cycles[6]["signal_schedule"] = ["function_call_weak_signal"]
    result = audit_perturbation_recovery(cycles)
    assert result["final_cycle_real_correctness_clean"] is True
    assert result["perturbation_recovery_audit_passed"] is True
