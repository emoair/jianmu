import json

from jianmu.self_learning.runtime.buffered_records import BufferedRecordConfig, BufferedRecordWriter


def test_buffered_records_flush_and_merge(tmp_path):
    runtime_dir = tmp_path / "runtime"
    final_dir = tmp_path / "records"
    writer = BufferedRecordWriter("run1", 0, BufferedRecordConfig(buffer_size=2, runtime_tmp_dir=str(runtime_dir), final_records_dir=str(final_dir)))
    writer.append({"record_type": "sample", "value": 1})
    writer.append({"record_type": "sample", "value": 2})
    summary = writer.close()
    merged = writer.merge_worker_shards()
    rows = [json.loads(line) for line in (final_dir / "merged_records.jsonl").read_text(encoding="utf-8").splitlines()]
    assert summary["buffered_record_count"] == 2
    assert len(rows) == 2
    assert merged["record_merge_time_seconds"] >= 0


def test_buffered_records_checkpoint_survives_partial_run(tmp_path):
    writer = BufferedRecordWriter("run1", 1, BufferedRecordConfig(buffer_size=10, runtime_tmp_dir=str(tmp_path / "runtime"), final_records_dir=str(tmp_path / "records")))
    writer.append({"record_type": "partial", "value": 1})
    checkpoint = writer.checkpoint()
    assert checkpoint.exists()
    assert "partial" in checkpoint.read_text(encoding="utf-8")

