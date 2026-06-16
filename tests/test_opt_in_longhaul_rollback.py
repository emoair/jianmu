from jianmu.self_learning.darwinforge.opt_in_longhaul_rollback import run_longhaul_rollback_review


def test_longhaul_rollback_detects_state_leak(tmp_path, monkeypatch):
    monkeypatch.setattr("jianmu.self_learning.darwinforge.opt_in_longhaul_rollback.run_opt_in_rollback_audit", lambda *args, **kwargs: {"opt_in_rollback_cycles": 1, "opt_in_cycle_pass_count": 0, "opt_in_cycle_fail_count": 1, "opt_out_blocks_bridge_after_each_cycle": False, "default_profile_after_each_cycle_unchanged": True, "arithmetic_baseline_after_each_cycle_clean": True, "production_flags_after_each_cycle_false": True, "opt_in_rollback_passed": False})
    result = run_longhaul_rollback_review(tmp_path, 1, 1)
    assert result["rollback_state_leak_detected"] is True
