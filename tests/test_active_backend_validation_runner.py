from jianmu.self_learning.darwinforge.active_backend_validation_runner import ShardedJsonlWriter


def test_active_backend_validation_requires_active_window_ratio(tmp_path) -> None:
    writer = ShardedJsonlWriter(tmp_path / "manifest.jsonl", max_bytes=80)
    for index in range(5):
        writer.write({"index": index, "payload": "x" * 40})
    writer.close()
    shards = list((tmp_path / "manifest").glob("*.jsonl"))
    assert len(shards) > 1
