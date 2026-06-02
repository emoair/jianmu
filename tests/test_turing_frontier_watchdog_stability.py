from jianmu.self_learning.darwinforge.turing_frontier_watchdog_stability import run_watchdog_stability


def test_watchdog_stability_no_fake_expected_output(tmp_path):
    result = run_watchdog_stability(tmp_path)
    assert result["watchdog_evaluator_clean"] is True
    assert result["wrong_halting_class_count"] == 0
    assert result["timeout_trace_integrity_passed"] is True
