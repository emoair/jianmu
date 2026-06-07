from pathlib import Path

from jianmu.self_learning.darwinforge.scale_trace_manifest_builder import write_scale_trace_pack


def test_scale_trace_manifest_builder_writes_jsonl(tmp_path):
    rows = [{"sample_id": "s", "sample_id_hash": "h", "policy": "p", "compile_invocation_id": "c", "cl_invoked": True, "link_invoked": True, "exe_run": True, "expected_stdout": "1", "actual_stdout": "1", "passed": True, "cached": False, "stubbed": False}]
    result = write_scale_trace_pack(tmp_path, rows, {"compiler_name": "cl"})
    assert result["trace_pack_generated"] is True
    assert Path(tmp_path / "scale_trace_pack" / "policy_path_trace_000.jsonl").exists()

