from jianmu.self_learning.runtime.highload_parallel_benchmark import HighLoadParallelBenchmarkConfig
from jianmu.self_learning.runtime.worker_scaling_benchmark import run_worker_scaling_benchmark


def test_worker_scaling_reports_all_worker_counts():
    samples = [{"sample_id": f"jm-v070-{i:06d}", "supported": i % 2 == 0} for i in range(12)]
    result = run_worker_scaling_benchmark(samples, HighLoadParallelBenchmarkConfig(mode="medium", worker_counts=[1, 2], seed=42))
    assert result["summary"]["worker_counts_tested"] == [1, 2]
    assert len(result["runs"]) == 2

