from jianmu.self_learning.darwinforge.opt_backend_manifest_binding import bind_opt_display_to_backend_manifest


def test_opt_backend_manifest_binding_requires_backend_counts(tmp_path) -> None:
    (tmp_path / "backend_invocation_manifest.jsonl").write_text('{"backend_cl_invocations": 1}\n', encoding="utf-8")
    (tmp_path / "opt_progress_trace.jsonl").write_text('{"backend_cl_invocations": 1}\n', encoding="utf-8")
    result = bind_opt_display_to_backend_manifest(tmp_path)
    assert result["opt_display_bound_to_backend_manifest"] is True
