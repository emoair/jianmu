from jianmu.self_learning.darwinforge.replay_trace_reader import build_replay_shard_index, read_trace_rows_from_index


def test_replay_trace_reader_avoids_full_rescan_per_worker(tmp_path):
    pack = tmp_path / "pack"
    pack.mkdir()
    (pack / "coverage_replay_policy_path_trace_000.jsonl").write_text('{"sample_id":"s"}\n', encoding="utf-8")
    index = build_replay_shard_index(pack)
    assert index["avoids_full_rescan_per_worker"] is True
    assert read_trace_rows_from_index(index)[0]["sample_id"] == "s"
