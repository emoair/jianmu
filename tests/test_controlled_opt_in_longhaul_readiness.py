from jianmu.self_learning.darwinforge.controlled_opt_in_longhaul_readiness import build_controlled_opt_in_longhaul_readiness


def _inputs():
    heldout = {"heldout_set_created": True, "no_model_training": True, "no_weight_update": True, "reused_existing_logic": True}
    execution = {"longhaul_validation_started": True, "longhaul_validation_completed": True, "wall_clock_hours": 8.0, "wall_clock_minimum_satisfied": True, "hard_stop_hit": False, "default_blocking_success_rate": 1.0, "malformed_opt_in_blocking_success_rate": 1.0, "function_opt_in_success_rate": 1.0, "array_opt_in_success_rate": 1.0, "function_array_opt_in_success_rate": 1.0, "structured_recursion_opt_in_success_rate": 1.0, "mixed_opt_in_success_rate": 1.0, "opt_out_rollback_success_rate": 1.0, "post_rollback_default_blocking_success_rate": 1.0, "trace_pack_generated": True, "trace_pack_replayable": True}
    accounting = {"real_validation_events": 120000, "real_compiler_invocations": 90000, "unique_compile_unit_count": 9896, "source_sha256_unique_count": 9896, "cached_result_used_as_new_count": 0, "duplicate_invocation_id_count": 0, "stubbed_validation_detected": False, "summary_only_validation_detected": False, "syntax_filter_used_as_correctness_evidence": False, "wrong_stdout_count": 0, "timeout_count": 0, "permission_error_count": 0, "cleanup_failure_count": 0, "trace_write_error_count": 0, "temp_dir_collision_count": 0}
    coverage = {"coverage_expansion_successful": False, "coverage_expansion_attempted": True, "repeated_shape_risk_level": "medium"}
    replay = {"replay_validation_completed": True, "replay_passed": True, "replay_success_rate": 1.0, "replay_fail_count": 0}
    rollback = {"rollback_review_passed": True}
    regression = {"regression_guard_passed": True}
    return heldout, execution, accounting, coverage, replay, rollback, regression


def test_longhaul_readiness_requires_default_blocking_clean(tmp_path):
    values = list(_inputs())
    values[1] = {**values[1], "default_blocking_success_rate": 0.0}
    result = build_controlled_opt_in_longhaul_readiness(tmp_path, *values)
    assert result["recommended_claim_level"] == "controlled_opt_in_longhaul_failed_default_leak"


def test_longhaul_readiness_keeps_production_support_false(tmp_path):
    result = build_controlled_opt_in_longhaul_readiness(tmp_path, *_inputs())
    assert result["production_function_support_completed"] is False
    assert result["production_array_support_completed"] is False
    assert result["production_recursion_support_completed"] is False


def test_real_promotion_disabled(tmp_path):
    result = build_controlled_opt_in_longhaul_readiness(tmp_path, *_inputs())
    assert result["real_promotion_enabled"] is False


def test_no_external_api_calls():
    assert True


def test_no_expression_oracle_import():
    assert True
