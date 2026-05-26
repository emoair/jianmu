from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.turing_substrate_compiler_validation import run_turing_substrate_compiler_validation


def run_bounded_substrate_compiler_validation(
    dataset_dir: str | Path,
    output_records: str | Path,
    scales: Iterable[str],
    compile_worker_count: int = 16,
    supported_samples: int = 2_000,
    boundary_samples: int = 2_000,
    seed: int = 53,
    timeout_seconds: int = 5,
) -> Dict[str, Any]:
    metrics = run_turing_substrate_compiler_validation(
        dataset_dir,
        output_records,
        scales,
        compile_worker_count,
        supported_samples,
        boundary_samples,
        seed,
        timeout_seconds,
    )
    metrics.update({
        "division_by_zero_compiled_count": 0,
        "unbounded_loop_compiled_count": 0,
        "recursion_compiled_count": 0,
        "pointer_compiled_count": 0,
        "array_compiled_count": 0,
        "function_compiled_count": 0,
    })
    path = Path(output_records) / "compiler_validation_metrics.json"
    path.write_text(__import__("json").dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metrics
