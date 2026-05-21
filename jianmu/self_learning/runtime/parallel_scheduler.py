from __future__ import annotations

import concurrent.futures
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List


@dataclass
class ParallelRuntimeConfig:
    worker_count: int = 8
    compile_worker_count: int = 4
    chunk_size: int = 64
    deterministic_order: bool = True
    seed: int = 42
    max_queue_size: int = 256
    fail_fast: bool = False
    collect_worker_errors: bool = True


@dataclass
class ParallelRunResult:
    completed: bool
    worker_count: int
    total_samples: int
    processed_samples: int
    failed_samples: int
    runtime_seconds: float
    samples_per_second: float
    worker_runtime_summary: Dict[str, Dict[str, float]]
    worker_error_count: int
    ordered_results: List[Any] = field(default_factory=list)
    worker_errors: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "completed": self.completed,
            "worker_count": self.worker_count,
            "total_samples": self.total_samples,
            "processed_samples": self.processed_samples,
            "failed_samples": self.failed_samples,
            "runtime_seconds": self.runtime_seconds,
            "samples_per_second": self.samples_per_second,
            "worker_runtime_summary": self.worker_runtime_summary,
            "worker_error_count": self.worker_error_count,
            "ordered_results": self.ordered_results,
            "worker_errors": self.worker_errors,
        }


def run_parallel_samples(samples: Iterable[Dict[str, Any]], worker_fn: Callable[[Dict[str, Any], int], Any], config: ParallelRuntimeConfig) -> ParallelRunResult:
    rows = list(samples)
    started = time.time()
    if config.worker_count <= 1:
        indexed = []
        errors = []
        worker_started = time.time()
        for index, sample in enumerate(rows):
            try:
                indexed.append((index, worker_fn(sample, config.seed)))
            except Exception as exc:  # pragma: no cover - exercised by tests with lightweight path
                errors.append(_error_row(0, sample, exc))
                if config.fail_fast:
                    raise
        return _finish(rows, indexed, errors, started, {0: time.time() - worker_started}, config)

    chunks = list(_chunks(list(enumerate(rows)), max(1, config.chunk_size)))
    indexed_results: List[tuple[int, Any]] = []
    errors: List[Dict[str, Any]] = []
    worker_times: Dict[int, float] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=config.worker_count) as executor:
        futures = []
        for chunk_index, chunk in enumerate(chunks):
            worker_id = chunk_index % config.worker_count
            worker_seed = config.seed + worker_id
            futures.append(executor.submit(_run_chunk, chunk, worker_fn, worker_id, worker_seed, config.fail_fast))
        for future in concurrent.futures.as_completed(futures):
            result_rows, error_rows, worker_id, runtime = future.result()
            indexed_results.extend(result_rows)
            errors.extend(error_rows)
            worker_times[worker_id] = worker_times.get(worker_id, 0.0) + runtime
            if errors and config.fail_fast:
                break
    return _finish(rows, indexed_results, errors, started, worker_times, config)


def _run_chunk(chunk, worker_fn, worker_id: int, worker_seed: int, fail_fast: bool):
    started = time.time()
    results = []
    errors = []
    for index, sample in chunk:
        try:
            results.append((index, worker_fn(sample, worker_seed)))
        except Exception as exc:
            errors.append(_error_row(worker_id, sample, exc))
            if fail_fast:
                raise
    return results, errors, worker_id, time.time() - started


def _finish(rows, indexed_results, errors, started, worker_times, config):
    if config.deterministic_order:
        indexed_results = sorted(indexed_results, key=lambda item: item[0])
    ordered_results = [value for _, value in indexed_results]
    runtime = round(time.time() - started, 6)
    processed = len(ordered_results)
    worker_summary = {
        str(worker_id): {"runtime_seconds": round(seconds, 6)}
        for worker_id, seconds in sorted(worker_times.items())
    }
    return ParallelRunResult(
        completed=len(errors) == 0,
        worker_count=config.worker_count,
        total_samples=len(rows),
        processed_samples=processed,
        failed_samples=len(errors),
        runtime_seconds=runtime,
        samples_per_second=round(processed / runtime, 6) if runtime > 0 else float(processed),
        worker_runtime_summary=worker_summary,
        worker_error_count=len(errors),
        ordered_results=ordered_results,
        worker_errors=errors if config.collect_worker_errors else [],
    )


def _chunks(rows, size):
    for index in range(0, len(rows), size):
        yield rows[index : index + size]


def _error_row(worker_id: int, sample: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
    return {
        "worker_id": worker_id,
        "sample_id": sample.get("sample_id"),
        "exception_type": type(exc).__name__,
        "traceback_summary": "".join(traceback.format_exception_only(type(exc), exc)).strip(),
    }

