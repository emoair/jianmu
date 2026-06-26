from jianmu.self_learning.darwinforge.opt_active_work_readiness import build_opt_active_work_readiness


def test_opt_active_work_readiness_keeps_production_false(tmp_path) -> None:
    payload = {
        "active_work_audit_completed": True,
        "opt_active_work_rate_contract_passed": True,
        "idle_padding_detector_passed": True,
        "opt_backend_consistency_audit_passed": True,
        "too_perfect_output_detector_passed": True,
        "git_residual_audit_passed": True,
        "git_cleanup_guard_passed": True,
        "trace_shard_size_cap_passed": True,
        "active_backend_validation_passed": True,
    }
    result = build_opt_active_work_readiness(tmp_path, payload)
    assert result["production_function_support_completed"] is False
    assert result["real_promotion_enabled"] is False
    assert result["recommended_claim_level"] == "opt_active_work_git_lifecycle_repaired"
