from jianmu.self_learning.darwinforge.opt_in_default_blocking_audit import run_opt_in_default_blocking_audit


def test_default_blocking_audit_blocks_function_without_opt_in(tmp_path):
    result = run_opt_in_default_blocking_audit(tmp_path)
    assert result["default_profile_function_bridge_reachable"] is False


def test_default_blocking_audit_blocks_array_without_opt_in(tmp_path):
    result = run_opt_in_default_blocking_audit(tmp_path)
    assert result["default_profile_array_bridge_reachable"] is False


def test_default_blocking_audit_blocks_recursion_without_opt_in(tmp_path):
    result = run_opt_in_default_blocking_audit(tmp_path)
    assert result["default_profile_recursion_bridge_reachable"] is False
