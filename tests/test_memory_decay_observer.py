from jianmu.self_learning.darwinforge.memory_decay_observer import observe_memory_decay


def test_memory_decay_observer_marks_file_cache(tmp_path) -> None:
    system_rows = [
        {"phase": "during", "used_physical_mb": 1000, "cache_bytes_mb": 500},
        {"phase": "after", "used_physical_mb": 995, "cache_bytes_mb": 490},
    ]
    result = observe_memory_decay(tmp_path, system_rows, [{"phase": "after", "process_tree_rss_mb": 10}], observation_seconds=180)
    assert result["likely_file_cache_or_standby"] is True
