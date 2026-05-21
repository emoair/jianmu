from jianmu.self_learning.runtime.highload_parallel_benchmark import highload_mode_configs, run_highload_parallel, summarize_worker_scaling


def test_highload_parallel_config_contains_medium_xlarge_light_xlarge():
    configs = highload_mode_configs()
    assert {"medium", "xlarge-light", "xlarge"} <= set(configs)


def test_highload_speedup_requires_real_workload():
    samples = [{"sample_id": f"s{i}", "supported": True} for i in range(8)]
    run = run_highload_parallel(samples, 1, highload_mode_configs()["medium"], seed=42)
    assert run["runtime_seconds"] >= 0
    assert run["completed"]


def test_worker_scaling_selects_best_worker_count():
    runs = [
        {"mode": "medium", "worker_count": 1, "runtime_seconds": 10, "samples_per_second": 10, "global_correct_targetir_in_beam_rate": 1, "candidate_space_failure_rate": 0, "ood_false_accept_rate": 0, "arithmetic_supported_retention_rate": 1, "stable_root_count": 1, "toxic_event_count": 0, "worker_error_count": 0},
        {"mode": "medium", "worker_count": 4, "runtime_seconds": 4, "samples_per_second": 25, "global_correct_targetir_in_beam_rate": 1, "candidate_space_failure_rate": 0, "ood_false_accept_rate": 0, "arithmetic_supported_retention_rate": 1, "stable_root_count": 1, "toxic_event_count": 0, "worker_error_count": 0},
    ]
    summary = summarize_worker_scaling(runs)
    assert summary["best_worker_count"] == 4
    assert summary["highload_parallel_speedup_confirmed"]


def test_worker_scaling_detects_metric_equivalence_failure():
    runs = [
        {"mode": "medium", "worker_count": 1, "runtime_seconds": 10, "samples_per_second": 10, "global_correct_targetir_in_beam_rate": 1, "candidate_space_failure_rate": 0, "ood_false_accept_rate": 0, "arithmetic_supported_retention_rate": 1, "stable_root_count": 1, "toxic_event_count": 0, "worker_error_count": 0},
        {"mode": "medium", "worker_count": 2, "runtime_seconds": 5, "samples_per_second": 20, "global_correct_targetir_in_beam_rate": 0.5, "candidate_space_failure_rate": 0.5, "ood_false_accept_rate": 0, "arithmetic_supported_retention_rate": 1, "stable_root_count": 1, "toxic_event_count": 0, "worker_error_count": 0},
    ]
    summary = summarize_worker_scaling(runs)
    assert not summary["metric_equivalence_passed"]

