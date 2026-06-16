from jianmu.self_learning.darwinforge.opt_in_longhaul_trace_builder import write_longhaul_trace_pack


def test_longhaul_trace_builder_shards_large_trace(tmp_path):
    row = {
        "sample_id": "s",
        "heldout_id": "h",
        "category": "default_blocking",
        "profile": "p",
        "explicit_opt_in": False,
        "policy": "default_profile_blocking_check",
        "compile_invocation_id": "c",
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
    result = write_longhaul_trace_pack(tmp_path, [row], [{"event_index": 1}], {"compiler_name": "cl"})
    assert result["trace_pack_replayable"] is True
