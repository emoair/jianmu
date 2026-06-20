from jianmu.self_learning.darwinforge.redqueen_iteration_trace import write_iteration_trace


def test_redqueen_iteration_trace_writes_jsonl(tmp_path):
    result = write_iteration_trace(tmp_path, [{"event_id": "a", "passed": True}, {"event_id": "b", "passed": True}])
    assert result["iteration_trace_generated"] is True
    assert (tmp_path / "redqueen_iteration_trace.jsonl").read_text(encoding="utf-8").count("\n") == 2
