from jianmu.self_learning.darwinforge.opt_in_rollback_audit import run_opt_in_rollback_audit


def test_opt_in_rollback_disables_bridge(tmp_path, monkeypatch):
    monkeypatch.setattr("jianmu.self_learning.darwinforge.opt_in_rollback_audit.execute_opt_in_request", lambda *args, **kwargs: {"passed": True, "explicit_opt_in": bool(args[4]), "compiler_invoked": bool(args[4])})
    monkeypatch.setattr("jianmu.self_learning.darwinforge.opt_in_rollback_audit.execute_with_backend", lambda *args, **kwargs: {"stdout_value_if_safe": 3})
    result = run_opt_in_rollback_audit(tmp_path, cycles=1, samples_per_cycle=1)
    assert result["opt_out_blocks_bridge_after_each_cycle"] is True
    assert result["opt_in_rollback_passed"] is True
