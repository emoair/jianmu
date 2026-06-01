from jianmu.self_learning.darwinforge.watchdog_evaluator import watchdog_evaluate


def test_watchdog_evaluator_timeout_unknown():
    result = watchdog_evaluate("unknown_growth", max_steps=3, timeout_ms=1)
    assert result["halting_class"] == "timeout_unknown"
    assert result["trace_truncated"] is True
