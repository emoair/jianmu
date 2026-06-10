from jianmu.self_learning.darwinforge.ir_c_stdout_alignment_review import generate_ir_c_stdout_alignment_review


def test_ir_c_stdout_alignment_generates_artifacts(tmp_path):
    sample = {"review_sample_id": "r0", "source_trace_id": "v1_0_5_1_function_00000194", "policy": "canonical_function_targetir", "ir_kind": "FunctionCallProgram", "builder": "build_function_program", "emitter": "ExtendedEmitterC", "source_sha256": "", "expected_stdout": "12", "actual_stdout": "12", "original_passed": True, "selected_reason": "test"}
    result = generate_ir_c_stdout_alignment_review(tmp_path, [sample], [{"review_sample_id": "r0", "actual_stdout": "12", "replay_passed": True}])
    assert result["alignment_review_completed"] is True
    assert (tmp_path / "review_samples" / "r0" / "emitted.c").exists()

