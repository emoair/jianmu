from jianmu.self_learning.darwinforge.trace_writer_shutdown_guard import verify_trace_writer_shutdown_guard


def test_trace_writer_shutdown_guard_flushes_and_closes(tmp_path):
    result = verify_trace_writer_shutdown_guard(tmp_path)
    assert result["trace_writer_shutdown_guard_passed"] is True
    assert result["file_handle_leak_count"] == 0
