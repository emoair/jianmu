from jianmu.self_learning.darwinforge.frontend_batchcompile_symbiote import run_scaleup_metrics


def test_frontend_batchcompile_symbiote_metrics(tmp_path):
    syntax = {"syntax_frontend_checked_count": 10, "syntax_frontend_pass_rate": 1.0}
    full = {"full_compile_invocation_count": 4, "compiler_verified_correctness_rate": 1.0, "wrong_stdout_count": 0, "watchdog_timeout_count": 1}
    function = {"function_success_rate": 0.927}
    array = {"array_success_rate": 0.924}
    interop = {"function_array_success_rate": 0.895}
    endurance = {"endurance_completed": True, "wall_clock_hours": 6.0, "rolling_window_count": 12}
    result = run_scaleup_metrics(tmp_path, syntax, full, function, array, interop, endurance)
    assert result["best_experiment_group"] == "redqueen_hydrabudget_symbiote_function_array_turing_mix"
