from jianmu.self_learning.darwinforge.batch_compile_failure_replay import write_failure_replay
from jianmu.self_learning.darwinforge.batch_compile_failure_taxonomy import write_failure_taxonomy


def test_failure_replay_runs_three_attempts(tmp_path):
    taxonomy = write_failure_taxonomy("records/v0_9_27", tmp_path)
    replay = write_failure_replay("records/v0_9_27", tmp_path, taxonomy)
    assert replay["replay_completed"] is True
    assert replay["replay_attempts_per_sample"] == 3
    assert replay["replay_total_attempts"] == taxonomy["unique_failed_sample_count"] * 3
