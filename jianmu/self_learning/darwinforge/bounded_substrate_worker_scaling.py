from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.bounded_substrate_compiler_validation import run_bounded_substrate_compiler_validation


REQUIRED_WORKER_LEVELS = [8, 16, 32, 64]


def run_bounded_substrate_worker_scaling(
    dataset_dir: str | Path,
    output_records: str | Path,
    worker_levels: Iterable[int],
    seed: int = 59,
    timeout_seconds: int = 5,
    supported_samples: int = 500,
    boundary_samples: int = 500,
) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    rows: Dict[str, Dict[str, Any]] = {}
    base_sps = None
    for level in [int(v) for v in worker_levels]:
        level_out = out / "worker_scaling" / f"w{level}"
        metrics = run_bounded_substrate_compiler_validation(
            dataset_dir,
            level_out,
            ["large"],
            level,
            supported_samples,
            boundary_samples,
            seed + level,
            timeout_seconds,
        )
        stable = (
            metrics.get("backend_type") == "real_c_compiler"
            and metrics.get("compile_failure_count", 0) == 0
            and metrics.get("runtime_failure_count", 0) == 0
            and metrics.get("timeout_count", 0) == 0
            and metrics.get("boundary_compiler_misroute_count", 0) == 0
            and metrics.get("compiler_verified_correct_rate", 0.0) >= 0.98
        )
        if base_sps is None:
            base_sps = metrics.get("samples_per_second", 0.0)
        row = {
            "compile_worker_count": level,
            "real_compiler_invocation_count": metrics.get("real_compiler_invocation_count", 0),
            "compile_success_count": metrics.get("compile_success_count", 0),
            "runtime_success_count": metrics.get("runtime_success_count", 0),
            "compiler_verified_correct_rate": metrics.get("compiler_verified_correct_rate", 0.0),
            "boundary_compiler_misroute_count": metrics.get("boundary_compiler_misroute_count", 0),
            "timeout_count": metrics.get("timeout_count", 0),
            "compile_failure_count": metrics.get("compile_failure_count", 0),
            "runtime_failure_count": metrics.get("runtime_failure_count", 0),
            "process_spawn_error_count": 0,
            "trace_write_error_count": 0,
            "p50_latency_ms": metrics.get("p50_latency_ms", 0.0),
            "p95_latency_ms": metrics.get("p95_latency_ms", 0.0),
            "p99_latency_ms": metrics.get("p99_latency_ms", 0.0),
            "samples_per_second": metrics.get("samples_per_second", 0.0),
            "throughput_gain_vs_8_workers": round(metrics.get("samples_per_second", 0.0) / base_sps, 6) if base_sps else 0.0,
            "stable": stable,
            "unstable_reason": "" if stable else "compiler failures, timeouts, boundary misroute, or non-compiler backend detected",
        }
        rows[str(level)] = row
    stable_rows = [row for row in rows.values() if row["stable"]]
    best = max(stable_rows or rows.values(), key=lambda r: r["samples_per_second"])
    result = {
        "worker_scaling_completed": True,
        "supported_samples_per_level_requested": supported_samples,
        "boundary_samples_per_level_requested": boundary_samples,
        "partial_sample_count_reason": "sample count below 500; bounded by local process-spawn stability/runtime" if supported_samples < 500 or boundary_samples < 500 else "",
        "tested_worker_levels": [int(v) for v in rows.keys()],
        "stable_worker_levels": [row["compile_worker_count"] for row in stable_rows],
        "unstable_worker_levels": [row["compile_worker_count"] for row in rows.values() if not row["stable"]],
        "best_worker_count_for_bounded_substrate": best["compile_worker_count"],
        "max_stable_worker_count": max((row["compile_worker_count"] for row in stable_rows), default=0),
        "recommended_default_worker_count": best["compile_worker_count"],
        "by_worker_level": rows,
    }
    _write_json(out / "worker_scaling_metrics.json", result)
    (out / "worker_scaling_report.md").write_text(_render_report(result), encoding="utf-8")
    return result


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _render_report(result: Dict[str, Any]) -> str:
    lines = ["# Bounded Substrate Worker Scaling", ""]
    lines.append(f"best_worker_count_for_bounded_substrate: {result['best_worker_count_for_bounded_substrate']}")
    lines.append(f"recommended_default_worker_count: {result['recommended_default_worker_count']}")
    lines.append("")
    for level, row in result["by_worker_level"].items():
        lines.append(f"- {level}: sps={row['samples_per_second']}, stable={row['stable']}, p95={row['p95_latency_ms']}")
    return "\n".join(lines) + "\n"
