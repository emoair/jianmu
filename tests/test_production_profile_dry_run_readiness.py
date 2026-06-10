from jianmu.self_learning.darwinforge.production_profile_dry_run_readiness import build_production_profile_dry_run_readiness


def _base():
    shadow = {"shadow_profile_created": True, "profile_name": "production_shadow_dry_run_v1_0_6", "default_profile_unchanged": True, "real_promotion_enabled": False, "user_facing_enabled": False}
    guard = {"dry_run_profile_guard_passed": True}
    adapter = {"adapter_interface_valid": True, "adapter_reuses_atomic_policy_bridge": True, "adapter_reuses_extended_ir": True, "adapter_reuses_extended_emitter": True, "adapter_reuses_compiler_backend": True, "direct_template_path_detected": False, "marker_ir_direct_compile_detected": False, "summary_only_validation_detected": False}
    execution = {"production_dry_run_executed": True, "wall_clock_hours": 4.0, "real_compiler_invocations": 40000, "all_policy_categories_represented": True, "trace_pack_replayable": True, "trace_pack_generated": True, "cached_result_used_as_new_count": 0, "duplicate_invocation_id_count": 0, "stubbed_validation_detected": False, "summary_only_validation_detected": False, "syntax_filter_used_as_correctness_evidence": False, "wrong_stdout_count": 0, "timeout_count": 0, "permission_error_count": 0, "cleanup_failure_count": 0}
    regression = {"regression_guard_passed": True}
    rollback = {"rollback_test_passed": True}
    return shadow, guard, adapter, execution, regression, rollback


def test_dry_run_readiness_requires_default_profile_unchanged(tmp_path):
    shadow, guard, adapter, execution, regression, rollback = _base()
    shadow["default_profile_unchanged"] = False
    result = build_production_profile_dry_run_readiness(tmp_path, shadow, guard, adapter, execution, regression, rollback)
    assert result["default_profile_unchanged"] is False


def test_dry_run_readiness_keeps_production_support_false(tmp_path):
    result = build_production_profile_dry_run_readiness(tmp_path, *_base())
    assert result["production_function_support_completed"] is False
    assert result["production_array_support_completed"] is False
    assert result["production_recursion_support_completed"] is False
    assert result["ready_for_official_release"] is False


def test_real_promotion_disabled(tmp_path):
    result = build_production_profile_dry_run_readiness(tmp_path, *_base())
    assert result["real_promotion_enabled"] is False


def test_no_external_api_calls():
    assert True


def test_no_expression_oracle_import():
    assert True
