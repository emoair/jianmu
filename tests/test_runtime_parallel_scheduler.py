import pytest

from jianmu.self_learning.runtime.parallel_scheduler import ParallelRuntimeConfig, run_parallel_samples


def test_parallel_scheduler_runs_with_worker_count_8():
    samples = [{"sample_id": f"s{i}", "value": i} for i in range(16)]
    result = run_parallel_samples(samples, lambda sample, seed: {"sample_id": sample["sample_id"], "value": sample["value"] + 1}, ParallelRuntimeConfig(worker_count=8, chunk_size=2))
    assert result.completed
    assert result.worker_count == 8
    assert result.processed_samples == 16


def test_parallel_scheduler_preserves_deterministic_order():
    samples = [{"sample_id": f"s{i}", "value": i} for i in range(20)]
    result = run_parallel_samples(samples, lambda sample, seed: sample["sample_id"], ParallelRuntimeConfig(worker_count=4, chunk_size=3, deterministic_order=True))
    assert result.ordered_results == [sample["sample_id"] for sample in samples]


def test_parallel_scheduler_records_worker_errors():
    samples = [{"sample_id": "ok"}, {"sample_id": "bad"}]

    def worker(sample, seed):
        if sample["sample_id"] == "bad":
            raise ValueError("boom")
        return sample["sample_id"]

    result = run_parallel_samples(samples, worker, ParallelRuntimeConfig(worker_count=2, chunk_size=1))
    assert not result.completed
    assert result.worker_error_count == 1
    assert result.worker_errors[0]["sample_id"] == "bad"

