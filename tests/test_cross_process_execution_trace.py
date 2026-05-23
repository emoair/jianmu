from jianmu.self_learning.darwinforge.cross_process_execution_trace import inspect_v0_9_1_cross_process, run_real_mini_cross_process_trace


def test_cross_process_trace_requires_child_eval_count(tmp_path):
    trace = inspect_v0_9_1_cross_process(tmp_path)
    assert trace["cross_process_trace_passed"] is False
    assert trace["child_eval_sample_count"] == 0


def test_real_mini_cross_process_trace_passes(tmp_path):
    trace = run_real_mini_cross_process_trace(tmp_path, 3)
    assert trace["cross_process_trace_passed"] is True
    assert trace["child_eval_sample_count"] == 3
