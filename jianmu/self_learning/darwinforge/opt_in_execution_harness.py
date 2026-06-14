from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.opt_in_compiler_validation import audit_opt_in_compiler_accounting
from jianmu.self_learning.darwinforge.opt_in_profile_adapter import execute_opt_in_request
from jianmu.self_learning.darwinforge.opt_in_trace_builder import write_opt_in_trace_pack
from jianmu.self_learning.darwinforge.staged_opt_in_profile_schema import StagedOptInProfileConfig


def run_opt_in_execution(
    output_records: str | Path,
    config: StagedOptInProfileConfig,
    targets: Dict[str, int],
    wall_clock_min_hours: float,
    max_runtime_hours: float,
    hard_stop_hours: float,
    minimum_real_validation_events: int,
    seed: int = 204,
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
        minimum_done = len(rows) >= minimum_real_validation_events
        wall_done = elapsed_hours >= wall_clock_min_hours
        if target_done and wall_done:
            break
        if elapsed_hours >= hard_stop_hours:
            hard_stop_hit = True
            break
        if elapsed_hours >= max_runtime_hours and minimum_done and wall_done:
            break
        kind = _next_kind(counters, targets, len(rows))
        explicit = kind not in {"default_blocking", "opt_out_rollback"}
        rows.append(execute_opt_in_request(counters[kind] + seed, kind, backend, config.profile_name, explicit, timeout_seconds=timeout_seconds))
        counters[kind] += 1
        if progress and time.perf_counter() - last_progress > 60:
            print(json.dumps({"opt_in_rows": len(rows), "elapsed_hours": round(elapsed_hours, 4), "kind": kind}, sort_keys=True), flush=True)
            last_progress = time.perf_counter()
    execution = _execution_metrics(rows, counters, targets, started, wall_clock_min_hours, hard_stop_hit, backend, config, workers_used)
    (out / "opt_in_execution_metrics.json").write_text(json.dumps(execution, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trace = write_opt_in_trace_pack(out, rows, {"backend_type": backend.backend_type, "compiler_name": backend.compiler_name, "compiler_environment": backend.compiler_environment})
    accounting = audit_opt_in_compiler_accounting(out, rows)
    return {**execution, **trace, **accounting}


def _next_kind(counters: Dict[str, int], targets: Dict[str, int], index: int) -> str:
    remaining = [kind for kind in targets if counters[kind] < targets[kind]]
    if remaining:
        return remaining[index % len(remaining)]
    return list(targets)[index % len(targets)]


def _execution_metrics(rows: List[Dict[str, Any]], counters: Dict[str, int], targets: Dict[str, int], started: float, wall_clock_min_hours: float, hard_stop_hit: bool, backend: Any, config: StagedOptInProfileConfig, workers_used: int) -> Dict[str, Any]:
    elapsed_hours = round((time.perf_counter() - started) / 3600.0, 6)
    return {
        "staged_opt_in_executed": True,
        "wall_clock_hours": elapsed_hours,
        "wall_clock_minimum_satisfied": elapsed_hours >= wall_clock_min_hours,
        "hard_stop_hit": hard_stop_hit,
        "category_counts": counters,
        "target_counts": targets,
        "all_opt_in_categories_represented": all(counters.get(kind, 0) > 0 for kind in ["function", "array", "function_array", "structured_recursion", "mixed"]),
        "default_blocking_categories_represented": counters.get("default_blocking", 0) > 0,
        "arithmetic_regression_compile_success_rate": _rate(rows, "arithmetic"),
        "function_opt_in_success_rate": _rate(rows, "function"),
        "array_opt_in_success_rate": _rate(rows, "array"),
        "function_array_opt_in_success_rate": _rate(rows, "function_array"),
        "structured_recursion_opt_in_success_rate": _rate(rows, "structured_recursion"),
        "mixed_opt_in_success_rate": _rate(rows, "mixed"),
        "opt_out_rollback_success_rate": _rate(rows, "opt_out_rollback"),
        "default_blocking_success_rate": _rate(rows, "default_blocking"),
        "compiler_verified_correctness_rate": round(sum(1 for row in rows if row["passed"]) / len(rows), 6) if rows else 0.0,
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "workers_requested": config.workers,
        "workers_used": workers_used,
        "downgrade_reason": "" if workers_used == config.workers else "capped_for_thread_safe_local_compiler_execution",
    }


def _rate(rows: List[Dict[str, Any]], kind: str) -> float:
    selected = [row for row in rows if row["request_kind"] == kind]
    return round(sum(1 for row in selected if row["passed"]) / len(selected), 6) if selected else 0.0
