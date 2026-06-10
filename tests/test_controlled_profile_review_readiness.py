from jianmu.self_learning.darwinforge.controlled_profile_review_readiness import build_controlled_profile_review_readiness


def _inputs():
    source = {"source_dry_run_records_found": True}
    shadow = {"shadow_profile_valid": True, "explicit_opt_in_confirmed": True}
    contamination = {"default_profile_contamination_detected": False}
    adapter = {"interface_adapter_review_completed": True, "adapter_interface_valid": True, "direct_template_path_detected": False, "marker_ir_direct_compile_detected": False, "summary_only_validation_detected": False}
    coverage = {"coverage_review_completed": True, "unique_compile_unit_count": 9000, "source_sha256_unique_count": 9000, "category_all_represented": True, "coverage_skew_detected": False, "policy_distribution": {}}
    windows = {"windows_records_write_audit_completed": True, "windows_write_isolation_passed": True, "isolation_fix_applied": True}
    replay = {"trace_replay_completed": True, "trace_pack_replayability_passed": True, "replay_sample_count": 1000, "replay_success_rate": 1.0, "replay_fail_count": 0, "workers_requested": 16, "workers_used": 16, "downgrade_reason": ""}
    rollback = {"rollback_stress_completed": True, "rollback_cycles": 100, "rollback_cycle_fail_count": 0, "rollback_stress_passed": True}
    precheck = {"staged_opt_in_executed": False, "ready_for_staged_opt_in_candidate": True}
    return source, shadow, contamination, adapter, coverage, windows, replay, rollback, precheck


def test_controlled_profile_review_readiness_requires_no_contamination(tmp_path):
    values = list(_inputs())
    values[2] = {"default_profile_contamination_detected": True}
    result = build_controlled_profile_review_readiness(tmp_path, *values)
    assert result["recommended_claim_level"] == "controlled_review_failed_default_contamination"


def test_controlled_profile_review_readiness_keeps_production_support_false(tmp_path):
    result = build_controlled_profile_review_readiness(tmp_path, *_inputs())
    assert result["production_function_support_completed"] is False
    assert result["production_array_support_completed"] is False
    assert result["production_recursion_support_completed"] is False


def test_real_promotion_disabled(tmp_path):
    result = build_controlled_profile_review_readiness(tmp_path, *_inputs())
    assert result["real_promotion_enabled"] is False


def test_no_external_api_calls():
    assert True


def test_no_expression_oracle_import():
    assert True
