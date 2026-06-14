from jianmu.self_learning.darwinforge.opt_in_execution_harness import _execution_metrics


def test_opt_in_execution_records_explicit_opt_in():
    rows = [{"request_kind": "function", "passed": True}]
    cfg = type("C", (), {"workers": 16})()
    backend = type("B", (), {"backend_type": "real_c_compiler", "compiler_name": "cl"})()
    metrics = _execution_metrics(rows, {"function": 1}, {"function": 1}, 0.0, 0.0, False, backend, cfg, 16)
    assert metrics["function_opt_in_success_rate"] == 1.0
