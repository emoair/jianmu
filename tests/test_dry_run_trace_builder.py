import json

from jianmu.self_learning.darwinforge.dry_run_trace_builder import write_dry_run_trace_pack


def test_dry_run_trace_builder_writes_sharded_trace(tmp_path):
    row = {
        "dry_run_sample_id": "s1",
        "sample_id_hash": "h",
        "shadow_profile": "production_shadow_dry_run_v1_0_6",
        "policy": "canonical_function_targetir",
        "compile_invocation_id": "c1",
        "cl_invoked": True,
        "link_invoked": True,
        "exe_run": True,
        "cached": False,
        "stubbed": False,
        "production_profile_modified": False,
        "real_promotion_enabled": False,
        "expected_stdout": "1",
        "actual_stdout": "1",
        "passed": True,
    }
    result = write_dry_run_trace_pack(tmp_path, [row], {"compiler_name": "cl"})
    assert result["trace_pack_replayable"] is True
    manifest = json.loads((tmp_path / "dry_run_trace_pack" / "dry_run_trace_manifest.json").read_text())
    assert manifest["total_rows"] == 1
