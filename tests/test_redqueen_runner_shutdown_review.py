from jianmu.self_learning.darwinforge.redqueen_runner_shutdown_review import review_redqueen_runner_shutdown


def test_redqueen_runner_shutdown_review_requires_idle_sentinel(tmp_path):
    result = review_redqueen_runner_shutdown(tmp_path, {"post_run_idle_sentinel_passed": False})
    assert result["runner_shutdown_review_passed"] is False
