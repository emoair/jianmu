from jianmu.self_learning.darwinforge.coverage_expansion_readiness import build_coverage_expansion_readiness


def _base():
    execution = {"wall_clock_hours": 4.0, "coverage_replay_completed": True}
    accounting = {"real_validation_events": 80000, "real_compiler_invocations": 50000, "wrong_stdout_count": 0, "timeout_count": 0, "permission_error_count": 0, "cleanup_failure_count": 0, "cached_result_used_as_new_count": 0, "duplicate_invocation_id_count": 0, "stubbed_validation_detected": False, "summary_only_validation_detected": False}
    review = {"new_unique_compile_unit_count": 12000, "new_source_sha256_unique_count": 12000, "category_all_represented": True}
    replay = {"replay_workers_used": 16, "replay_downgraded": False, "replay_16_worker_passed": True}
    guard = {"default_profile_unchanged": True, "explicit_opt_in_required": True, "default_blocking_passed": True, "malformed_opt_in_blocking_passed": True, "opt_out_rollback_passed": True, "post_rollback_default_blocking_passed": True, "regression_guard_passed": True, "default_profile_bridge_leak_detected": False}
    trace = {"trace_pack_replayable": True, "trace_pack_generated": True}
    repair = {"replay_concurrency_repair_completed": True}
    return execution, accounting, review, replay, guard, trace, repair


def test_coverage_expansion_readiness_requires_12000_unique_units(tmp_path):
    execution, accounting, review, replay, guard, trace, repair = _base()
    review["new_unique_compile_unit_count"] = 11999
    result = build_coverage_expansion_readiness(tmp_path, {"reused_existing_logic": True}, execution, accounting, review, replay, guard, trace, repair)
    assert result["recommended_claim_level"] != "coverage_expansion_replay_concurrency_positive"


def test_coverage_expansion_readiness_requires_16_worker_replay(tmp_path):
    execution, accounting, review, replay, guard, trace, repair = _base()
    replay["replay_workers_used"] = 1
    replay["replay_downgraded"] = True
    result = build_coverage_expansion_readiness(tmp_path, {"reused_existing_logic": True}, execution, accounting, review, replay, guard, trace, repair)
    assert result["recommended_claim_level"] != "coverage_expansion_replay_concurrency_positive"


def test_coverage_expansion_readiness_keeps_production_support_false(tmp_path):
    result = build_coverage_expansion_readiness(tmp_path, {"reused_existing_logic": True}, *_base())
    assert result["production_function_support_completed"] is False
    assert result["ready_for_official_release"] is False
