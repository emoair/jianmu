from jianmu.self_learning.darwinforge.streaming_manifest_writer import StreamingManifestWriter, write_streaming_manifest_contract


def test_streaming_manifest_writer_rotates_shards(tmp_path) -> None:
    writer = StreamingManifestWriter(tmp_path / "manifest.jsonl", max_shard_size_bytes=90, flush_interval_rows=1)
    for i in range(10):
        writer.write({"i": i, "payload": "x" * 50})
    writer.close()
    shards = list((tmp_path / "manifest").glob("*.jsonl"))
    assert len(shards) > 1
    assert write_streaming_manifest_contract(tmp_path, writer)["streaming_manifest_writer_passed"] is True
