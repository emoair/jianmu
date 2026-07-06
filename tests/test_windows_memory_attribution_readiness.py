from jianmu.self_learning.darwinforge.windows_memory_attribution_readiness import build_windows_memory_attribution_readiness


def test_windows_memory_attribution_readiness_handles_inconclusive(tmp_path) -> None:
    payload = {
        "system_memory_sampler_passed": True,
        "process_tree_sampler_passed": True,
        "top_process_snapshot_passed": True,
        "classifier_passed": True,
        "artifact_cache_audit_passed": True,
        "workload_replay_passed": True,
        "decay_observer_passed": True,
        "attribution_completed": True,
        "runner_rss_peak_mb": 20,
        "runner_python_heap_peak_mb": 5,
        "process_tree_peak_rss_mb": 20,
    }
    result = build_windows_memory_attribution_readiness(tmp_path, payload)
    assert result["recommended_claim_level"] == "windows_memory_attribution_inconclusive"
    assert result["production_function_support_completed"] is False


def test_windows_memory_attribution_readiness_reports_external_throughput_pressure(tmp_path) -> None:
    payload = {
        "system_memory_sampler_passed": True,
        "process_tree_sampler_passed": True,
        "top_process_snapshot_passed": True,
        "classifier_passed": True,
        "artifact_cache_audit_passed": True,
        "workload_replay_passed": False,
        "workload_replay_completed": True,
        "compiler_verified_correctness_rate": 1.0,
        "wrong_stdout_count": 0,
        "timeout_count": 0,
        "decay_observer_passed": True,
        "attribution_completed": True,
        "runner_rss_peak_mb": 26,
        "runner_python_heap_peak_mb": 5,
        "process_tree_peak_rss_mb": 100,
        "ide_git_activity_detected": True,
    }
    result = build_windows_memory_attribution_readiness(tmp_path, payload)
    assert result["recommended_claim_level"] == "windows_memory_attribution_completed_fix_required"
    assert result["workload_replay_throughput_blocked_by_external_pressure"] is True
    assert result["blocking_issues"] == []
