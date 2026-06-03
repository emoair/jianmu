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


def test_full_compile_50k_requires_total_50000(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    previous = core.previous_clean_evidence(inputs, core._previous_sources(inputs), core.missing_input_records(inputs))
    continuation = {
        "new_continuation_invocations": 29999,
        "new_continuation_completed": False,
        "new_continuation_clean": False,
        "partial_reason": "one short",
        "compiler_verified_correctness_rate_new": 1.0,
        "new_wrong_stdout_count": 0,
        "new_timeout_count": 0,
        "new_permission_error_count": 0,
        "new_cleanup_failure_count": 0,
        "boundary_compiler_misroute_count_new": 0,
        "future_domain_compiled_count_new": 0,
        "recursion_production_compiled_count_new": 0,
        "pointer_compiled_count_new": 0,
        "io_compiled_count_new": 0,
    }
    payload = core.write_continuation(inputs, previous, continuation)
    assert payload["total_accounted_invocations"] == 49999
    assert payload["full_compile_50k_clean"] is False


def test_full_compile_50k_clean_requires_zero_failures(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    previous = core.previous_clean_evidence(inputs, core._previous_sources(inputs), core.missing_input_records(inputs))
    continuation = {
        "new_continuation_invocations": 30000,
        "new_continuation_completed": True,
        "new_continuation_clean": False,
        "partial_reason": None,
        "compiler_verified_correctness_rate_new": 0.999,
        "new_wrong_stdout_count": 1,
        "new_timeout_count": 0,
        "new_permission_error_count": 0,
        "new_cleanup_failure_count": 0,
        "boundary_compiler_misroute_count_new": 0,
        "future_domain_compiled_count_new": 0,
        "recursion_production_compiled_count_new": 0,
        "pointer_compiled_count_new": 0,
        "io_compiled_count_new": 0,
    }
    payload = core.write_continuation(inputs, previous, continuation)
    assert payload["total_accounted_invocations"] == 50000
    assert payload["wrong_stdout_count_total"] == 1
    assert payload["full_compile_50k_clean"] is False
