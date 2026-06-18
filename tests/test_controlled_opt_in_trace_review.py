from jianmu.self_learning.darwinforge.controlled_opt_in_trace_review import build_controlled_support_trace_pack


def test_controlled_opt_in_trace_review_generates_trace_pack(tmp_path):
    positive = [{
        "sample_id": "p1",
        "category": "function",
        "policy": "canonical_function_targetir",
        "atomic_policy": "canonical_function_targetir",
        "builder": "builder",
        "ir_kind": "FunctionCallProgram",
        "emitter": "ExtendedEmitterC",
        "source_sha256": "abc",
        "compile_invocation_id": "cid",
        "compiler_invoked": True,
        "link_invoked": True,
        "exe_run": True,
        "expected_stdout": "1",
        "actual_stdout": "1",
        "passed": True,
    }]
    negative = [{
        "sample_id": "n1",
        "category": "unknown_policy_rejection",
        "passed": True,
        "compile_invoked": False,
    }]
    result = build_controlled_support_trace_pack(tmp_path, positive, negative, {"compiler_name": "cl"})
    assert result["trace_pack_generated"] is True
    assert result["trace_pack_replayable"] is True
    assert (tmp_path / "controlled_support_trace_pack" / "support_candidate_trace_manifest.json").exists()
