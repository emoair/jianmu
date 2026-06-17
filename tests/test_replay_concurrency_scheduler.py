from jianmu.self_learning.darwinforge.replay_concurrency_scheduler import assign_replay_shards


def test_replay_concurrency_scheduler_uses_16_workers():
    index = {"shards": [{"path": f"s{i}.jsonl"} for i in range(3)]}
    result = assign_replay_shards(index, 16)
    assert result["replay_workers_used"] == 16
    assert result["replay_downgraded"] is False
