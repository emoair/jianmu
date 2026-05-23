from jianmu.self_learning.darwinforge.workload_trace import WorkloadTraceRecorder, summarize_workload_trace


def test_workload_trace_records_real_execution(tmp_path):
    trace = WorkloadTraceRecorder("quick", 42)
    trace.record("train_iteration", "fn", 1, "s1", real_execution=True)
    path = tmp_path / "trace.jsonl"
    trace.write_jsonl(path)
    summary = summarize_workload_trace(trace.events)
    assert summary["real_execution_event_count"] == 1
    assert summary["sample_count_total"] == 1


def test_workload_trace_marks_summary_path():
    trace = WorkloadTraceRecorder("quick", 42)
    trace.record("comparison_pack", "summary", 0, real_execution=False, synthetic_or_summary_path=True)
    summary = summarize_workload_trace(trace.events)
    assert summary["synthetic_summary_event_count"] == 1
