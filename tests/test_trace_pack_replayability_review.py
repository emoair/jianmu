from jianmu.self_learning.darwinforge.trace_pack_replayability_review import _replay_one


def test_trace_pack_replayability_review_detects_stdout_drift(monkeypatch):
    def fake_execute(index, kind, backend, shadow):
        return {"actual_stdout": "bad", "passed": True, "source_sha256": "s", "builder": "b", "emitter": "e", "ir_kind": "i", "link_invoked": True, "timeout": False}

    monkeypatch.setattr("jianmu.self_learning.darwinforge.trace_pack_replayability_review.execute_shadow_profile_request", fake_execute)
    row = {"dry_run_sample_id": "v1_0_6_function_00000001", "policy": "canonical_function_targetir", "expected_stdout": "ok", "source_sha256": "s", "builder": "b", "emitter": "e", "ir_kind": "i", "shadow_profile": "p"}
    result = _replay_one(row, object())
    assert result["stdout_mismatch"] is True
