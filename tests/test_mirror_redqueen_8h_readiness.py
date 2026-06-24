from jianmu.self_learning.darwinforge.mirror_redqueen_8h_readiness import build_mirror_redqueen_8h_readiness


def test_mirror_redqueen_8h_readiness_keeps_production_false(tmp_path) -> None:
    payload = {
        "preflight_truth_gate_passed": True,
        "true_time_integrity_audit_passed": True,
        "lane_swap_stability_audit_passed": True,
        "frozen_lane_integrity_audit_passed": True,
        "feedback_loop_audit_passed": True,
        "lifecycle_guard_passed": True,
        "actual_elapsed_seconds": 28800,
        "cycles_completed": 8,
        "total_events": 160000,
        "real_compiler_invocations": 110000,
        "compiler_verified_correctness_rate": 1.0,
        "wrong_stdout_count": 0,
        "timeout_count": 0,
        "distribution_audit_passed": True,
        "over_under_reaction_audit_passed": True,
        "real_compile_lane_passed": True,
        "governance_safety_audit_passed": True,
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
    }
    result = build_mirror_redqueen_8h_readiness(tmp_path, payload)
    assert result["recommended_claim_level"] == "mirror_redqueen_cosymbiosis_true_8h_positive"
    assert result["production_function_support_completed"] is False
    assert result["redqueen_autonomous_governance_completed"] is False

