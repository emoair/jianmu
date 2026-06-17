import json

from jianmu.self_learning.darwinforge.replay_concurrency_repair import write_replay_concurrency_repair_report


def test_replay_concurrency_repair_creates_shard_index(tmp_path):
    pack = tmp_path / "pack"
    pack.mkdir()
    (pack / "coverage_replay_policy_path_trace_000.jsonl").write_text(json.dumps({"sample_id": "s"}) + "\n", encoding="utf-8")
    result = write_replay_concurrency_repair_report(tmp_path, pack, 16)
    assert result["shard_index_created"] is True
    assert result["replay_concurrency_ready"] is True
