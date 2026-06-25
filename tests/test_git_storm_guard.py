from jianmu.self_learning.darwinforge.git_storm_guard import run_git_storm_guard


def test_git_storm_guard_detects_mass_untracked_artifacts(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    for i in range(101):
        (tmp_path / f"{i}.obj").write_text("x", encoding="utf-8")
    result = run_git_storm_guard(tmp_path / "records", tmp_path)
    assert result["worktree_compiler_artifacts_detected"] is True
    assert result["git_storm_detected"] is True
