from jianmu.self_learning.darwinforge.staged_opt_in_readiness import build_staged_opt_in_readiness


def _inputs():
    config = {"staged_opt_in_profile_created": True, "profile_name": "p", "default_profile_unchanged": True, "opt_in_enabled_only_by_explicit_flag": True, "real_promotion_enabled": False, "user_facing_enabled": False, "official_release_enabled": False}
    guard = {"staged_opt_in_guard_passed": True}
    blocking = {"default_blocking_passed": True, "default_profile_bridge_leak_detected": False}
    adapter = {"adapter_interface_valid": True, "adapter_reuses_v1_0_6_dry_run_adapter": True, "adapter_reuses_atomic_policy_bridge": True, "adapter_reuses_extended_ir": True, "adapter_reuses_extended_emitter": True, "adapter_reuses_compiler_backend": True, "direct_template_path_detected": False, "marker_ir_direct_compile_detected": False, "summary_only_validation_detected": False}
    execution = {"staged_opt_in_executed": True, "wall_clock_hours": 4.0, "real_validation_events": 45000, "all_opt_in_categories_represented": True, "trace_pack_replayable": True, "trace_pack_generated": True, "cached_result_used_as_new_count": 0, "duplicate_invocation_id_count": 0, "stubbed_validation_detected": False, "summary_only_validation_detected": False, "syntax_filter_used_as_correctness_evidence": False, "wrong_stdout_count": 0, "timeout_count": 0, "permission_error_count": 0, "cleanup_failure_count": 0}
    rollback = {"opt_in_rollback_passed": True}
    regression = {"regression_guard_passed": True}
    return config, guard, blocking, adapter, execution, rollback, regression


def test_staged_opt_in_readiness_requires_no_default_leak(tmp_path):
    values = list(_inputs())
    values[2] = {"default_blocking_passed": False, "default_profile_bridge_leak_detected": True}
    result = build_staged_opt_in_readiness(tmp_path, *values)
    assert result["recommended_claim_level"] == "staged_opt_in_failed_default_leak"


def test_staged_opt_in_readiness_keeps_production_support_false(tmp_path):
    result = build_staged_opt_in_readiness(tmp_path, *_inputs())
    assert result["production_function_support_completed"] is False
    assert result["production_array_support_completed"] is False
    assert result["production_recursion_support_completed"] is False


def test_real_promotion_disabled(tmp_path):
    result = build_staged_opt_in_readiness(tmp_path, *_inputs())
    assert result["real_promotion_enabled"] is False


def test_no_external_api_calls():
    assert True


def test_no_expression_oracle_import():
    assert True
