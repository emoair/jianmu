from jianmu.self_learning.darwinforge.mirror_redqueen_lifecycle_guard import run_mirror_redqueen_lifecycle_guard


def test_lifecycle_guard_requires_idle_sentinel(tmp_path) -> None:
    result = run_mirror_redqueen_lifecycle_guard(tmp_path, tmp_path / "out", idle_grace_seconds=0)
    assert result["lifecycle_guard_completed"] is True
    assert "final_post_run_idle_sentinel_passed" in result

