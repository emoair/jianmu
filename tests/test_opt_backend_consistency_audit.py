import json

from jianmu.self_learning.darwinforge.opt_backend_consistency_audit import audit_opt_backend_consistency


def test_opt_backend_consistency_audit_detects_counter_mismatch(tmp_path) -> None:
    manifest = tmp_path / "manifest.jsonl"
    manifest.write_text(json.dumps({"compile_invocation_id": "a"}) + "\n", encoding="utf-8")
    progress = tmp_path / "progress.jsonl"
    progress.write_text(json.dumps({"backend_cl_invocations": 2, "backend_cl_delta": 1, "backend_exe_delta": 1, "last_backend_age_sec": 0, "compiler_verified_correctness_rate": 1.0, "security_status": "clean", "git_guard": "clean", "artifact_root": "tmp"}) + "\n", encoding="utf-8")
    result = audit_opt_backend_consistency(tmp_path, manifest_path=manifest, progress_path=progress)
    assert result["opt_counts_match_backend_manifest"] is False
    assert result["opt_backend_consistency_audit_passed"] is False
