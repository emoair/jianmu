from pathlib import Path

from jianmu.self_learning.darwinforge import full_compile_50k_continuation_core as core


def _inputs(tmp_path: Path) -> core.FullCompile50KInputs:
    return core.FullCompile50KInputs(
        records_root=Path("records"),
        source_records_v27_1=Path("records/v0_9_27_1"),
        source_records_v28=Path("records/v0_9_28"),
        source_datasets=[],
        output_records=tmp_path,
    )


def test_readiness_release_false(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    sources = core._previous_sources(inputs)
    previous = core.previous_clean_evidence(inputs, sources, core.missing_input_records(inputs))
    cont = {
        "continuation_completed": True,
        "new_continuation_invocations": 30000,
        "total_accounted_invocations": 50000,
        "full_compile_50k_clean": True,
        "compiler_verified_correctness_rate_total": 1.0,
        "wrong_stdout_count_total": 0,
        "timeout_count_total": 0,
        "permission_error_count_total": 0,
        "cleanup_failure_count_total": 0,
        "boundary_compiler_misroute_count_total": 0,
        "future_domain_compiled_count_total": 0,
        "recursion_production_compiled_count_total": 0,
        "pointer_compiled_count_total": 0,
        "io_compiled_count_total": 0,
    }
    readiness = core.write_readiness(inputs, sources, previous, {"total_accounting_clean": True}, cont, {"postflight_passed": True}, {"charter_guard_passed": True}, [])
    assert readiness["ready_for_v1_0_rc1_branch"] is True
    assert readiness["ready_for_v1_0_release"] is False
    assert readiness["recommended_claim_level"] == "frontier_review_50k_clean_ready_for_v1_0_rc1"


def test_architecture_charter_guard_no_new_capability(tmp_path: Path) -> None:
    guard = core.write_architecture_charter_guard(tmp_path)
    assert guard["no_new_production_capability"] is True
    assert guard["real_promotion_disabled"] is True
    assert guard["default_profile_unchanged"] is True
