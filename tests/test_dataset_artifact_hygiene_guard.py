from jianmu.self_learning.darwinforge.dataset_artifact_hygiene_guard import run_dataset_artifact_hygiene_guard


def test_dataset_artifact_hygiene_guard_blocks_worktree_dataset(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    root = tmp_path / "dataset"
    root.mkdir()
    result = run_dataset_artifact_hygiene_guard(tmp_path / "records", root)
    assert result["dataset_artifacts_outside_worktree"] is False
    assert result["repo_hygiene_guard_passed"] is False
