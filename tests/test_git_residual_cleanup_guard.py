from jianmu.self_learning.darwinforge.git_residual_cleanup_guard import run_git_residual_cleanup_guard


def test_git_residual_cleanup_guard_requires_no_index_lock(tmp_path) -> None:
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "index.lock").write_text("", encoding="utf-8")
    result = run_git_residual_cleanup_guard(tmp_path, worktree=tmp_path, idle_wait_seconds=0)
    assert result["index_lock_removed_or_absent"] is True
