from jianmu.self_learning.darwinforge.memory_queue_guard import memory_queue_guard


def test_memory_queue_guard_uses_streaming_jsonl(tmp_path) -> None:
    result = memory_queue_guard(tmp_path, queue_peak_size=2, rss_peak_mb=10)
    assert result["streaming_jsonl_enabled"] is True
    assert result["no_giant_manifest_list"] is True
    assert result["memory_guard_passed"] is True
