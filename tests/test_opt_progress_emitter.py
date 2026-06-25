from io import StringIO

from jianmu.self_learning.darwinforge.opt_progress_emitter import OptProgressEmitter


def test_opt_progress_emitter_flushes_lines(tmp_path) -> None:
    stream = StringIO()
    emitter = OptProgressEmitter(tmp_path / "trace.jsonl", tmp_path / "stdout.log")
    line = emitter.emit({"actual_elapsed_seconds": 1, "backend_cl_invocations": 1, "backend_link_invocations": 1, "backend_exe_runs": 1, "artifact_root": "tmp", "security_status": "clean"}, stream=stream)
    assert "[OPT]" in line
    assert "backend_cl=1" in stream.getvalue()
    assert (tmp_path / "trace.jsonl").read_text(encoding="utf-8")
    assert (tmp_path / "stdout.log").read_text(encoding="utf-8")
