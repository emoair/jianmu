from pathlib import Path

from jianmu.self_learning.darwinforge.artifact_out_of_worktree_guard import artifact_guard


def test_artifact_out_of_worktree_guard_blocks_worktree_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / "bad.obj").write_text("x", encoding="utf-8")
    result = artifact_guard(tmp_path / "records", tmp_path / "inside")
    assert result["artifact_guard_passed"] is False


def test_artifact_out_of_worktree_guard_allows_temp(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    artifact_root = Path.cwd().parent / "artifact_temp"
    result = artifact_guard(tmp_path / "records", artifact_root)
    assert result["artifact_root_outside_worktree"] is True
