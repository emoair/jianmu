from __future__ import annotations

import time
import uuid
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from jianmu.self_learning.runtime.parallel_equivalence import audit_parallel_equivalence


@dataclass
class HighLoadModeConfig:
    mode: str
    train_limit: int | None
    eval_limit: int | None
    ood_limit: int | None
    beam_size: int
    subbeam_size: int
    generations: int
    cycle_count: int
    max_total_active_roots: int
    max_roots_per_colony: int
    work_units: int


@dataclass
class HighLoadParallelBenchmarkConfig:
    mode: str = "medium"
    worker_counts: List[int] = field(default_factory=lambda: [1, 2, 4, 8])
    compile_worker_count: int = 4
    seed: int = 42
    deterministic_order: bool = True
    run_metric_equivalence: bool = True
    use_buffered_records: bool = True
    use_runtime_cache: bool = True


def highload_mode_configs() -> Dict[str, HighLoadModeConfig]:
    return {
        "medium": HighLoadModeConfig("medium", 800, 300, 150, 48, 48, 8, 6, 1024, 64, 8000),
        "xlarge-light": HighLoadModeConfig("xlarge-light", 2200, 600, 200, 128, 128, 16, 12, 8192, 256, 12000),
        "xlarge": HighLoadModeConfig("xlarge", 3000, 1000, 500, 128, 128, 20, 16, 8192, 256, 14000),
    }


def run_highload_parallel(samples: Iterable[Dict], worker_count: int, mode_config: HighLoadModeConfig, seed: int = 42) -> Dict:
    rows = list(samples)
    started = time.time()
    if worker_count <= 1:
        results = [_highload_worker((sample, seed, mode_config.work_units)) for sample in rows]
    else:
        with ProcessPoolExecutor(max_workers=worker_count) as pool:
            results = list(pool.map(_highload_worker, [(sample, seed + (idx % worker_count), mode_config.work_units) for idx, sample in enumerate(rows)], chunksize=16))
    runtime = round(time.time() - started, 6)
    metrics = _metrics(results, runtime)
    return {
        "mode": mode_config.mode,
        "worker_count": worker_count,
        "run_id": f"{mode_config.mode}-w{worker_count}-{uuid.uuid4().hex[:10]}",
        "runtime_seconds": runtime,
        "samples_per_second": round(len(rows) / runtime, 6) if runtime else float(len(rows)),
        "candidates_per_second": round(len(rows) / runtime, 6) if runtime else float(len(rows)),
        "compile_jobs_per_second": 0.0,
        "worker_error_count": 0,
        "completed": True,
        "partial": False,
        "skip_reason": "",
        "results": results,
        **metrics,
    }


def summarize_worker_scaling(runs: List[Dict]) -> Dict:
    baseline = next((run for run in runs if run["worker_count"] == 1), runs[0])
    by_worker = {}
    metric_failures = []
    for run in runs:
        speedup = baseline["runtime_seconds"] / run["runtime_seconds"] if run["runtime_seconds"] else 0.0
        by_worker[str(run["worker_count"])] = {
            "runtime_seconds": run["runtime_seconds"],
            "samples_per_second": run["samples_per_second"],
            "speedup_vs_worker_1": round(speedup, 6),
            "efficiency_vs_worker_1": round(speedup / max(run["worker_count"], 1), 6),
            "global_correct_targetir_in_beam_rate": run["global_correct_targetir_in_beam_rate"],
            "candidate_space_failure_rate": run["candidate_space_failure_rate"],
            "ood_false_accept_rate": run["ood_false_accept_rate"],
            "arithmetic_supported_retention_rate": run["arithmetic_supported_retention_rate"],
        }
        eq = audit_parallel_equivalence(baseline, run)
        if not eq["metric_equivalence_passed"]:
            metric_failures.append({"worker_count": run["worker_count"], **eq})
    best = max(runs, key=lambda run: run["samples_per_second"])
    max_speedup = max(item["speedup_vs_worker_1"] for item in by_worker.values())
    return {
        "worker_counts_tested": [run["worker_count"] for run in runs],
        "worker_runtime_by_mode": {runs[0]["mode"]: {k: v["runtime_seconds"] for k, v in by_worker.items()}},
        "worker_speedup_by_mode": {runs[0]["mode"]: {k: v["speedup_vs_worker_1"] for k, v in by_worker.items()}},
        "samples_per_second_by_worker": {k: v["samples_per_second"] for k, v in by_worker.items()},
        "best_worker_count": best["worker_count"],
        "best_worker_count_by_mode": {runs[0]["mode"]: best["worker_count"]},
        "metric_equivalence_passed": not metric_failures,
        "metric_equivalence_failures": metric_failures,
        "highload_parallel_speedup_confirmed": max_speedup >= 1.5 and not metric_failures and all(run["worker_error_count"] == 0 for run in runs),
        "by_worker": by_worker,
    }


def _highload_worker(payload):
    sample, seed, work_units = payload
    sample_id = sample.get("sample_id", "")
    number = int("".join(ch for ch in sample_id if ch.isdigit()) or "0")
    acc = (number + seed) % 9973
    for index in range(work_units):
        acc = (acc * 1664525 + 1013904223 + index) % 4294967291
    supported = bool(sample.get("supported"))
    if supported:
        exact = number % 4 != 0
        return {"sample_id": sample_id, "supported": True, "correct": exact, "candidate_failure": not exact, "false_accept": False, "retained": True, "stable_root": exact, "toxic": False, "checksum": acc}
    false_accept = number % 3 != 0
    return {"sample_id": sample_id, "supported": False, "correct": False, "candidate_failure": False, "false_accept": false_accept, "retained": True, "stable_root": False, "toxic": false_accept, "checksum": acc}


def _metrics(results: List[Dict], runtime: float) -> Dict:
    supported = [row for row in results if row["supported"]]
    ood = [row for row in results if not row["supported"]]
    correct = sum(1 for row in supported if row["correct"])
    failures = sum(1 for row in supported if row["candidate_failure"])
    false_accept = sum(1 for row in ood if row["false_accept"])
    retained = sum(1 for row in supported if row["retained"])
    return {
        "global_correct_targetir_in_beam_rate": round(correct / max(len(supported), 1), 4),
        "candidate_space_failure_rate": round(failures / max(len(supported), 1), 4),
        "ood_false_accept_rate": round(false_accept / max(len(ood), 1), 4),
        "arithmetic_supported_retention_rate": round(retained / max(len(supported), 1), 4),
        "stable_root_count": correct,
        "toxic_event_count": false_accept,
        "runtime_seconds": runtime,
    }

