from jianmu.self_learning.darwinforge.redqueen_multiround_stability_lifecycle import run_stability_lifecycle_guard


def test_redqueen_multiround_lifecycle_guard_requires_idle_sentinel(tmp_path):
    result = run_stability_lifecycle_guard(tmp_path, tmp_path, {"cycles": [{"lifecycle": {"cycle_lifecycle_checkpoint_passed": True}}]}, idle_grace_seconds=0)
    assert result["multiround_lifecycle_guard_completed"] is True
    assert "final_post_run_idle_sentinel_passed" in result
