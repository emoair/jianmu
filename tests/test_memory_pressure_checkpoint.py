from jianmu.self_learning.darwinforge.memory_pressure_checkpoint import build_memory_pressure_checkpoint


def test_memory_pressure_checkpoint_writes_partial_records(tmp_path) -> None:
    result = build_memory_pressure_checkpoint(tmp_path, rss_peak_mb=80, warning_threshold_mb=70, hard_threshold_mb=100, partial_payload={"ok": True})
    assert result["memory_warning_triggered"] is True
    assert result["memory_hard_stop_triggered"] is False
    assert result["emergency_checkpoint_written"] is True
