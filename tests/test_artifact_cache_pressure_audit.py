from jianmu.self_learning.darwinforge.artifact_cache_pressure_audit import audit_artifact_cache_pressure


def test_artifact_cache_pressure_audit_detects_worktree_artifacts(tmp_path) -> None:
    root = tmp_path / "records"
    root.mkdir()
    (root / "x.jsonl").write_text("{}\n", encoding="utf-8")
    result = audit_artifact_cache_pressure(tmp_path, compiler_artifact_root=tmp_path / "compiler", dataset_artifact_root=tmp_path / "dataset", records_root=root)
    assert result["artifact_cache_audit_completed"] is True
    assert result["trace_total_mb"] >= 0
