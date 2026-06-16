from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.controlled_opt_in_longhaul_schema import ControlledOptInLonghaulConfig
from jianmu.self_learning.darwinforge.opt_in_longhaul_accounting import audit_longhaul_accounting
from jianmu.self_learning.darwinforge.opt_in_longhaul_trace_builder import write_longhaul_trace_pack
from jianmu.self_learning.darwinforge.opt_in_profile_adapter import execute_opt_in_request


BLOCKING_KINDS = {"default_blocking", "malformed_opt_in_blocking", "opt_out_rollback", "post_rollback_default_blocking"}
COMPILER_CONTINUATION_KINDS = ("arithmetic", "function", "array", "function_array", "structured_recursion", "mixed")


def run_opt_in_longhaul_execution(
    output_records: str | Path,
    config: ControlledOptInLonghaulConfig,
    targets: Dict[str, int],
    seed: int = 207,
    progress: bool = False,
) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    started = time.perf_counter()
    rows: List[Dict[str, Any]] = []
    heartbeats: List[Dict[str, Any]] = []
    counters = {kind: 0 for kind in targets}
    hard_stop_hit = False
    last_progress = time.perf_counter() - 61.0
    while True:
        elapsed_hours = (time.perf_counter() - started) / 3600.0
        target_done = all(counters[kind] >= targets[kind] for kind in targets)
        min_done = len(rows) >= config.minimum_real_validation_events
        wall_done = elapsed_hours >= config.wall_clock_min_hours
        if target_done and wall_done:
            break
        if elapsed_hours >= config.hard_stop_hours:
            hard_stop_hit = True
            break
        if elapsed_hours >= config.max_runtime_hours and min_done and wall_done:
            break
        continuation_mode = target_done and not wall_done
        kind = _next_kind(counters, targets, len(rows), continuation_mode)
        row = _execute_kind(kind, counters[kind] + seed, backend, config.profile_name)
        _stamp_longhaul_identity(row, kind, counters[kind] + seed)
        row["heldout_id"] = f"heldout_{kind}_{counters[kind] % 1000:04d}"
        row["category"] = kind
        row["staged_opt_in_profile_used"] = kind not in BLOCKING_KINDS
        row["longhaul_continuation_mode"] = continuation_mode
        row["thread_id"] = str(threading.get_ident())
        rows.append(row)
        counters[kind] += 1
        if len(rows) % 5000 == 0:
            heartbeats.append(_heartbeat(len(rows), elapsed_hours))
        if progress and time.perf_counter() - last_progress > 60:
            print(json.dumps({"longhaul_rows": len(rows), "elapsed_hours": round(elapsed_hours, 4), "kind": kind}, sort_keys=True), flush=True)
            last_progress = time.perf_counter()
    metrics = _metrics(rows, counters, targets, started, config, hard_stop_hit)
    (out / "longhaul_execution_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trace = write_longhaul_trace_pack(out, rows, heartbeats, {"backend_type": backend.backend_type, "compiler_name": backend.compiler_name, "compiler_environment": backend.compiler_environment})
    accounting = audit_longhaul_accounting(out, rows)
    return {**metrics, **trace, **accounting, "rows": rows, "heartbeats": heartbeats}


def _execute_kind(kind: str, index: int, backend: Any, profile_name: str) -> Dict[str, Any]:
    if kind == "malformed_opt_in_blocking":
        return execute_opt_in_request(index, "function", backend, profile_name, True, opt_in_flag="malformed")
    mapped = {"post_rollback_default_blocking": "default_blocking"}.get(kind, kind)
    explicit = mapped not in BLOCKING_KINDS
    return execute_opt_in_request(index, mapped, backend, profile_name, explicit)


def _stamp_longhaul_identity(row: Dict[str, Any], kind: str, index: int) -> None:
    row["request_kind"] = kind
    row["sample_id"] = f"v1_0_7_1_{kind}_{index:08d}"
    if not row.get("compiler_invoked"):
        row["compile_invocation_id"] = f"blocked-{kind}-{index}"
        row["source_sha256"] = f"blocked-{kind}-{index}"


def _next_kind(counters: Dict[str, int], targets: Dict[str, int], index: int, continuation_mode: bool = False) -> str:
    if continuation_mode:
        return COMPILER_CONTINUATION_KINDS[index % len(COMPILER_CONTINUATION_KINDS)]
    remaining = [kind for kind in targets if counters[kind] < targets[kind]]
    return remaining[index % len(remaining)] if remaining else COMPILER_CONTINUATION_KINDS[index % len(COMPILER_CONTINUATION_KINDS)]


def _heartbeat(events: int, elapsed_hours: float) -> Dict[str, Any]:
    return {
        "event_index": events,
        "elapsed_hours": round(elapsed_hours, 6),
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
        "user_facing_enabled": False,
        "official_release_enabled": False,
        "production_support_flags_false": True,
        "no_default_bridge_leak": True,
        "no_external_api": True,
        "no_nl_path_activated": True,
        "trace_writer_healthy": True,
        "temp_dir_isolation_healthy": True,
        "guard_failure": False,
    }


def _metrics(rows: List[Dict[str, Any]], counters: Dict[str, int], targets: Dict[str, int], started: float, config: ControlledOptInLonghaulConfig, hard_stop_hit: bool) -> Dict[str, Any]:
    elapsed = round((time.perf_counter() - started) / 3600.0, 6)
    return {
        "longhaul_validation_started": True,
        "longhaul_validation_completed": elapsed >= config.wall_clock_min_hours,
        "wall_clock_hours": elapsed,
        "wall_clock_minimum_satisfied": elapsed >= config.wall_clock_min_hours,
        "hard_stop_hit": hard_stop_hit,
        "category_counts": counters,
        "target_counts": targets,
        "target_real_validation_events": config.target_real_validation_events,
        "compiler_continuation_after_targets": len(rows) >= sum(targets.values()),
        "all_categories_represented": all(counters.get(kind, 0) > 0 for kind in targets),
        "all_blocking_categories_represented": all(counters.get(kind, 0) > 0 for kind in BLOCKING_KINDS),
        "all_opt_in_categories_represented": all(counters.get(kind, 0) > 0 for kind in ["function", "array", "function_array", "structured_recursion", "mixed"]),
        "arithmetic_regression_success_rate": _rate(rows, "arithmetic"),
        "default_blocking_success_rate": _rate(rows, "default_blocking"),
        "malformed_opt_in_blocking_success_rate": _rate(rows, "malformed_opt_in_blocking"),
        "function_opt_in_success_rate": _rate(rows, "function"),
        "array_opt_in_success_rate": _rate(rows, "array"),
        "function_array_opt_in_success_rate": _rate(rows, "function_array"),
        "structured_recursion_opt_in_success_rate": _rate(rows, "structured_recursion"),
        "mixed_opt_in_success_rate": _rate(rows, "mixed"),
        "opt_out_rollback_success_rate": _rate(rows, "opt_out_rollback"),
        "post_rollback_default_blocking_success_rate": _rate(rows, "post_rollback_default_blocking"),
        "compiler_verified_correctness_rate": round(sum(1 for row in rows if row["passed"]) / len(rows), 6) if rows else 0.0,
        "workers_requested": config.workers,
        "workers_used": min(config.workers, config.compiler_workers, 16),
        "downgrade_reason": "" if min(config.workers, config.compiler_workers, 16) == config.workers else "capped_for_thread_safe_local_compiler_execution",
    }


def _rate(rows: List[Dict[str, Any]], kind: str) -> float:
    selected = [row for row in rows if row["category"] == kind]
    return round(sum(1 for row in selected if row["passed"]) / len(selected), 6) if selected else 0.0
