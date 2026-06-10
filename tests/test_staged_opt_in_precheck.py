from jianmu.self_learning.darwinforge.staged_opt_in_precheck import run_staged_opt_in_precheck


def test_staged_opt_in_precheck_does_not_execute_staged_opt_in(tmp_path):
    result = run_staged_opt_in_precheck(tmp_path, True)
    assert result["staged_opt_in_executed"] is False
    assert result["staged_opt_in_enabled"] is False
    assert result["ready_for_staged_opt_in_candidate"] is True
