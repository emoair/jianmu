import json

from jianmu.self_learning.darwinforge.memory_snapshot_tracker import MemorySnapshotTracker


def test_memory_snapshot_tracker_records_tracemalloc(tmp_path) -> None:
    tracker = MemorySnapshotTracker(tmp_path / "timeline.jsonl")
    tracker.snapshot("unit", queue_size=0, writer_buffer_size=1)
    tracker.close()
    row = json.loads((tmp_path / "timeline.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert row["rss_mb"] >= 0
    assert "python_heap_peak_mb" in row
    assert tracker.contract(tmp_path)["memory_snapshot_contract_passed"] is True
