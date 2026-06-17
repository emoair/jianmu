from jianmu.self_learning.darwinforge.replay_worker_isolation import sample_temp_dir, verify_worker_isolation


def test_replay_worker_isolation_uses_per_sample_temp_dirs():
    assert sample_temp_dir("a", 1) != sample_temp_dir("a", 2)
    assert verify_worker_isolation("a", 16)["per_sample_temp_dir_confirmed"] is True
