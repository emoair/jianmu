from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.dry_run_compiler_validation import audit_dry_run_compiler_accounting
from jianmu.self_learning.darwinforge.dry_run_trace_builder import write_dry_run_trace_pack
from jianmu.self_learning.darwinforge.production_profile_dry_run_schema import ProductionProfileDryRunConfig
from jianmu.self_learning.darwinforge.production_profile_interface_adapter import execute_shadow_profile_request


def run_dry_run_execution(
    output_records: str | Path,
    config: ProductionProfileDryRunConfig,
    targets: Dict[str, int],
    wall_clock_min_hours: float,
    max_runtime_hours: float,
    hard_stop_hours: float,
    minimum_real_compiler_invocations: int,
    seed: int = 198,
    timeout_seconds: int = 5,
    progress: bool = False,
) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    started = time.perf_counter()
    rows: List[Dict[str, Any]] = []
    counters = {kind: 0 for kind in targets}
    hard_stop_hit = False
    workers_used = max(1, min(config.workers, config.compiler_workers, 16))
    last_progress = 0.0
    while True:
        elapsed_hours = (time.perf_counter() - started) / 3600.0
        target_done = all(counters[kind] >= targets[kind] for kind in targets)
        minimum_done = len(rows) >= minimum_real_compiler_invocations
        wall_done = elapsed_hours >= wall_clock_min_hours
        if target_done and wall_done:
            break
        if elapsed_hours >= hard_stop_hours:
            hard_stop_hit = True
            break
        if elapsed_hours >= max_runtime_hours and minimum_done and wall_done:
            break
        kind = _next_kind(counters, targets, len(rows))
        rows.append(execute_shadow_profile_request(counters[kind] + seed, kind, backend, config.profile_name, timeout_seconds))
        counters[kind] += 1
        if progress and time.perf_counter() - last_progress > 60:
            print(json.dumps({"dry_run_rows": len(rows), "elapsed_hours": round(elapsed_hours, 4), "kind": kind}, sort_keys=True), flush=True)
            last_progress = time.perf_counter()
    execution = _execution_metrics(rows, counters, targets, started, wall_clock_min_hours, hard_stop_hit, backend, config, workers_used)
    (out / "dry_run_execution_metrics.json").write_text(json.dumps(execution, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trace = write_dry_run_trace_pack(out, rows, {"backend_type": backend.backend_type, "compiler_name": backend.compiler_name, "compiler_environment": backend.compiler_environment})
    accounting = audit_dry_run_compiler_accounting(out, rows)
    return {**execution, **trace, **accounting}


def _next_kind(counters: Dict[str, int], targets: Dict[str, int], index: int) -> str:
    remaining = [kind for kind in targets if counters[kind] < targets[kind]]
    if remaining:
        return remaining[index % len(remaining)]
    return list(targets)[index % len(targets)]


def _execution_metrics(rows: List[Dict[str, Any]], counters: Dict[str, int], targets: Dict[str, int], started: float, wall_clock_min_hours: float, hard_stop_hit: bool, backend: Any, config: ProductionProfileDryRunConfig, workers_used: int) -> Dict[str, Any]:
    elapsed_hours = round((time.perf_counter() - started) / 3600.0, 6)
    return {
        "production_dry_run_executed": True,
        "wall_clock_hours": elapsed_hours,
        "wall_clock_minimum_satisfied": elapsed_hours >= wall_clock_min_hours,
        "hard_stop_hit": hard_stop_hit,
        "category_counts": counters,
        "target_counts": targets,
        "all_policy_categories_represented": all(counters.get(kind, 0) > 0 for kind in targets),
        "arithmetic_regression_compile_success_rate": _rate(rows, "arithmetic"),
        "function_dry_run_success_rate": _rate(rows, "function"),
        "array_dry_run_success_rate": _rate(rows, "array"),
        "function_array_dry_run_success_rate": _rate(rows, "function_array"),
        "structured_recursion_dry_run_success_rate": _rate(rows, "structured_recursion"),
        "mixed_dry_run_success_rate": _rate(rows, "mixed"),
        "compiler_verified_correctness_rate": round(sum(1 for row in rows if row["passed"]) / len(rows), 6) if rows else 0.0,
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "workers_requested": config.workers,
        "workers_used": workers_used,
        "downgrade_reason": "" if workers_used == config.workers else "capped_for_thread_safe_local_compiler_execution",
    }


def _rate(rows: List[Dict[str, Any]], kind: str) -> float:
    selected = [row for row in rows if row["dry_run_sample_id"].startswith(f"v1_0_6_{kind}_")]
    return round(sum(1 for row in selected if row["passed"]) / len(selected), 6) if selected else 0.0
