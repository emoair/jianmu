from jianmu.self_learning.runtime.parallel_equivalence import audit_parallel_equivalence
from jianmu.self_learning.runtime.runtime_profiler import RuntimeProfiler


def test_parallel_equivalence_passes_for_same_seed():
    metrics = {
        "global_correct_targetir_in_beam_rate": 0.5,
        "candidate_space_failure_rate": 0.5,
        "ood_false_accept_rate": 0.2,
        "arithmetic_supported_retention_rate": 1.0,
        "stable_root_count": 10,
        "toxic_event_count": 2,
        "runtime_seconds": 10,
    }
    result = audit_parallel_equivalence(metrics, dict(metrics, runtime_seconds=5))
    assert result["metric_equivalence_passed"]
    assert result["speedup_ratio"] == 2


def test_parallel_equivalence_detects_metric_delta():
    serial = {"global_correct_targetir_in_beam_rate": 0.5}
    parallel = {"global_correct_targetir_in_beam_rate": 0.6}
    result = audit_parallel_equivalence(serial, parallel)
    assert not result["metric_equivalence_passed"]
    assert "global_correct_targetir_in_beam_rate" in result["differing_metric_names"]


def test_runtime_profiler_reports_basic_sections():
    profiler = RuntimeProfiler()
    with profiler.section("sample_eval"):
        pass
    report = profiler.report(sample_count=10)
    assert "sample_eval_time_seconds" in report
    assert report["estimated_cpu_utilization_note"] == "not_measured"

