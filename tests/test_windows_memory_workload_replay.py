from jianmu.self_learning.darwinforge.windows_memory_attribution_readiness import build_windows_memory_attribution_report


def test_windows_memory_attribution_report_inconclusive(tmp_path) -> None:
    result = build_windows_memory_attribution_report(tmp_path, {"runner_rss_peak_mb": 20, "runner_python_heap_peak_mb": 5, "process_tree_peak_rss_mb": 20})
    assert result["primary_attribution"] == "inconclusive"
    assert result["unaccounted_memory_pressure_detected"] is True
