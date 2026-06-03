from jianmu.self_learning.darwinforge.frontend_filter_accounting import write_frontend_accounting


def test_frontend_filter_accounting(tmp_path):
    syntax = {"syntax_frontend_checked_count": 10, "syntax_frontend_pass_count": 9, "syntax_frontend_fail_count": 1}
    full = {"full_compile_invocation_count": 4, "full_compile_success_count": 4, "runtime_success_count": 4, "stdout_correct_count": 4, "watchdog_timeout_count": 2}
    result = write_frontend_accounting(tmp_path, syntax, full)
    assert result["syntax_frontend_accounting"]["syntax_check_count"] == 10
    assert result["full_compile_accounting"]["stdout_correct_count"] == 4
    assert result["syntax_filter_used_as_correctness_evidence"] is False
