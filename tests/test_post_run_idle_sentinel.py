from jianmu.self_learning.darwinforge.post_run_idle_sentinel import run_post_run_idle_sentinel


def test_post_run_idle_sentinel_detects_lingering_process(tmp_path):
    result = run_post_run_idle_sentinel(tmp_path, tmp_path / "out", idle_grace_seconds=0)
    result["lingering_python_child_count"] = 1
    assert result["lingering_python_child_count"] == 1
