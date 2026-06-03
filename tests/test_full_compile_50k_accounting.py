from pathlib import Path

from jianmu.self_learning.darwinforge.full_compile_50k_continuation_core import FullCompile50KInputs, previous_clean_evidence, _previous_sources, missing_input_records


def _inputs(tmp_path: Path) -> FullCompile50KInputs:
    return FullCompile50KInputs(
        records_root=Path("records"),
        source_records_v27_1=Path("records/v0_9_27_1"),
        source_records_v28=Path("records/v0_9_28"),
        source_datasets=[],
        output_records=tmp_path,
    )


def test_full_compile_50k_accounting_previous_clean(tmp_path: Path) -> None:
    inputs = _inputs(tmp_path)
    previous = previous_clean_evidence(inputs, _previous_sources(inputs), missing_input_records(inputs))
    assert previous["previous_clean_invocations"] == 20000
    assert previous["previous_compiler_correctness"] == 1.0
    assert previous["previous_clean_evidence_valid"] is True


def test_full_compile_50k_no_cached_result_as_new(tmp_path: Path) -> None:
    from jianmu.self_learning.darwinforge.full_compile_50k_continuation_core import write_accounting

    inputs = _inputs(tmp_path)
    previous = previous_clean_evidence(inputs, _previous_sources(inputs), missing_input_records(inputs))
    accounting = write_accounting(inputs, previous, {"new_continuation_invocations": 0})
    assert accounting["cached_result_used_as_new_count"] == 0
    assert accounting["duplicate_invocation_id_count"] == 0
