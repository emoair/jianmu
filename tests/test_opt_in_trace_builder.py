import json

from jianmu.self_learning.darwinforge.opt_in_trace_builder import write_opt_in_trace_pack


def test_opt_in_trace_builder_writes_default_blocking_trace(tmp_path):
    row = {
        "sample_id": "s1",
        "profile": "p",
        "explicit_opt_in": False,
        "policy": "default_profile_blocking_check",
        "request_kind": "default_blocking",
        "compile_invocation_id": "c1",
        "cl_invoked": False,
        "link_invoked": False,
        "exe_run": False,
        "cached": False,
        "stubbed": False,
        "default_profile_modified": False,
        "real_promotion_enabled": False,
        "expected_stdout": "blocked",
        "actual_stdout": "blocked",
        "passed": True,
    }
    result = write_opt_in_trace_pack(tmp_path, [row], {"compiler_name": "cl"})
    assert result["trace_pack_replayable"] is True
    assert (tmp_path / "opt_in_trace_pack" / "opt_in_default_blocking_trace.jsonl").exists()
