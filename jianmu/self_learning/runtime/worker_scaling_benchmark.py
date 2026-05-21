from __future__ import annotations

from typing import Dict, List

from jianmu.self_learning.runtime.highload_parallel_benchmark import HighLoadParallelBenchmarkConfig, highload_mode_configs, run_highload_parallel, summarize_worker_scaling


def run_worker_scaling_benchmark(samples: List[Dict], config: HighLoadParallelBenchmarkConfig) -> Dict:
    mode_config = highload_mode_configs()[config.mode]
    runs = [run_highload_parallel(samples, count, mode_config, seed=config.seed) for count in config.worker_counts]
    summary = summarize_worker_scaling(runs)
    return {"runs": runs, "summary": summary}

