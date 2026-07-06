import sys

from jianmu.self_learning.darwinforge.subprocess_output_streaming import run_process_streaming, write_subprocess_output_streaming_contract


def test_subprocess_output_streaming_does_not_buffer_large_output(tmp_path) -> None:
    out = tmp_path / "stdout.txt"
    err = tmp_path / "stderr.txt"
    result = run_process_streaming([sys.executable, "-c", "print('x' * 10000)"], tmp_path, out, err, max_preview_bytes=10)
    assert result["returncode"] == 0
    assert len(result["stdout_preview"]) <= 10
    assert out.stat().st_size > 10000
    assert write_subprocess_output_streaming_contract(tmp_path)["subprocess_output_streaming_passed"] is True
