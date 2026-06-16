from jianmu.self_learning.darwinforge.opt_in_longhaul_replay import _replay_one


def test_longhaul_replay_detects_policy_path_drift(monkeypatch):
    monkeypatch.setattr("jianmu.self_learning.darwinforge.opt_in_longhaul_replay._execute_kind", lambda *args, **kwargs: {"actual_stdout": "1", "passed": True, "source_sha256": "s", "builder": "other", "emitter": "e", "ir_kind": "i", "link_invoked": True, "timeout": False})
    row = {"sample_id": "sample_00000001", "category": "function", "profile": "p", "policy": "canonical_function_targetir", "expected_stdout": "1", "source_sha256": "s", "builder": "b", "emitter": "e", "ir_kind": "i", "compiler_invoked": True}
    assert _replay_one(row, object())["policy_path_drift"] is True
