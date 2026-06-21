from jianmu.self_learning.darwinforge.redqueen_endurance_lifecycle_guard import run_endurance_lifecycle_guard


def test_redqueen_endurance_lifecycle_guard_requires_idle_sentinel(tmp_path):
    result = run_endurance_lifecycle_guard(tmp_path, tmp_path, {"cycles": [{"lifecycle": {"cycle_lifecycle_checkpoint_passed": True}}]}, idle_grace_seconds=0)
    assert result["final_post_run_idle_sentinel_passed"] is True
