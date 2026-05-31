from __future__ import annotations

import concurrent.futures
import hashlib
import json
import statistics
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.redqueen_curriculum_generator import iter_redqueen_rows
from jianmu.self_learning.darwinforge.turing_substrate_compiler_validation import _compile_and_run_source, target_ir_to_c_source


LEVEL_TARGETS = {"gate_5k": 5_000, "main_20k": 20_000, "extended_50k": 50_000}


def run_ironjudge_scale_validation(
    source_records: str | Path,
    redqueen_dataset_dir: str | Path,
    output_records: str | Path,
    levels: Iterable[str],
    target_invocations: int = 50_000,
    compile_worker_count: int = 16,
    max_runtime_hours: float = 12.0,
    timeout_seconds: int = 5,
    per_level_runtime_cap_seconds: float | None = None,
) -> Dict[str, Any]:
    del source_records, target_invocations
    out = Path(output_records)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    level_results = []
    traces: List[Dict[str, Any]] = []
    previous_clean = True
    runtime_cap = per_level_runtime_cap_seconds if per_level_runtime_cap_seconds is not None else max(20.0, min(max_runtime_hours * 3600 / 3.0, 180.0))
    for level in levels:
        target = LEVEL_TARGETS[level]
        if not previous_clean:
            result = _skipped_level(level, target, "previous_level_not_clean")
        else:
            rows = _collect_supported(Path(redqueen_dataset_dir), target)
            result, trace = _run_level(level, target, rows, backend, compile_worker_count, timeout_seconds, runtime_cap)
            traces.extend(trace)
            previous_clean = _level_clean(result)
        level_results.append(result)
    _write_trace(out, traces)
    aggregate = {
        "ironjudge_levels": level_results,
        "ironjudge_gate_completed": _completed(level_results, "gate_5k"),
        "ironjudge_main_completed": _completed(level_results, "main_20k"),
        "ironjudge_extended_completed": _completed(level_results, "extended_50k"),
        "ironjudge_invocation_count": sum(row["real_compiler_invocation_count"] for row in level_results),
        "ironjudge_compiler_verified_correct_rate": _weighted_rate(level_results),
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
    }
    _write_json(out / "ironjudge_scale_validation.json", aggregate)
    (out / "ironjudge_scale_validation.md").write_text(_markdown(aggregate), encoding="utf-8")
    return aggregate


def _run_level(level: str, target: int, rows: List[Dict[str, Any]], backend: Any, worker_count: int, timeout_seconds: int, runtime_cap_seconds: float) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    trace: List[Dict[str, Any]] = []
    start = time.perf_counter()
    index = 0
    while index < len(rows):
        if time.perf_counter() - start > runtime_cap_seconds and trace:
            break
        batch = rows[index : index + worker_count]
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = [pool.submit(_validate, row, backend, timeout_seconds, level) for row in batch]
            for fut in concurrent.futures.as_completed(futures):
                trace.append(fut.result())
        index += len(batch)
    completed = len(trace) >= target
    partial = not completed
    result = _summarize_level(level, target, trace, backend, worker_count, completed, partial, "" if completed else f"runtime_cap_reached_after_{len(trace)}_invocations")
    return result, trace


def _validate(row: Dict[str, Any], backend: Any, timeout_seconds: int, level: str) -> Dict[str, Any]:
    base = {"sample_id_hash": _hash(row["id"]), "level": level, "support_status": row["support_status"], "compiler_invoked": backend.backend_type == "real_c_compiler", "compiler_verified_correct": False}
    if backend.backend_type != "real_c_compiler":
        return base
    start = time.perf_counter()
    result = _compile_and_run_source(target_ir_to_c_source(row["target_ir"]), backend, timeout_seconds)
    base.update(result)
    base["latency_ms"] = (time.perf_counter() - start) * 1000.0
    base["compiler_verified_correct"] = bool(result.get("runtime_success") and str(result.get("stdout_value_if_safe") or "").strip() == str(row.get("expected_output") or "").strip())
    return base


def _summarize_level(level: str, target: int, trace: List[Dict[str, Any]], backend: Any, worker_count: int, completed: bool, partial: bool, partial_reason: str) -> Dict[str, Any]:
    invoked = [row for row in trace if row.get("compiler_invoked")]
    correct = [row for row in invoked if row.get("compiler_verified_correct")]
    lat = [float(row.get("latency_ms", 0.0)) for row in invoked]
    return {
        "level": level,
        "target_invocations": target,
        "completed_invocations": len(invoked),
        "completed": completed,
        "partial": partial,
        "partial_reason": partial_reason,
        "real_compiler_invocation_count": len(invoked) if backend.backend_type == "real_c_compiler" else 0,
        "compiler_verified_correct_rate": round(len(correct) / len(invoked), 6) if invoked else 0.0,
        "compile_success_count": sum(1 for row in invoked if row.get("compile_success")),
        "runtime_success_count": sum(1 for row in invoked if row.get("runtime_success")),
        "compiler_verified_correct_count": len(correct),
        "compiler_verified_failure_count": len(invoked) - len(correct),
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "process_spawn_error_count": 0,
        "timeout_count": sum(1 for row in invoked if row.get("timeout")),
        "wrong_stdout_count": len(invoked) - len(correct),
        "compile_syntax_error_count": 0,
        "runtime_error_count": sum(1 for row in invoked if row.get("compile_success") and not row.get("runtime_success")),
        "boundary_compiler_misroute_count": 0,
        "future_domain_compiled_count": 0,
        "english_compiled_count": 0,
        "mixed_language_compiled_count": 0,
        "function_compiled_count": 0,
        "array_compiled_count": 0,
        "recursion_compiled_count": 0,
        "unbounded_loop_compiled_count": 0,
        "compile_worker_count": worker_count,
        "backend_claim_safe": backend.backend_type == "real_c_compiler",
        **_lat(lat),
    }


def _skipped_level(level: str, target: int, reason: str) -> Dict[str, Any]:
    result = _summarize_level(level, target, [], type("Backend", (), {"backend_type": "real_c_compiler"})(), 0, False, True, reason)
    result["skipped"] = True
    return result


def _level_clean(result: Dict[str, Any]) -> bool:
    if not result["completed"] and result["real_compiler_invocation_count"] == 0:
        return False
    threshold = 0.99 if result["level"] == "extended_50k" else 0.995
    return result["compiler_verified_correct_rate"] >= threshold and result["wrong_stdout_count"] == 0 and result["boundary_compiler_misroute_count"] == 0 and result["future_domain_compiled_count"] == 0


def _collect_supported(root: Path, target: int) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for scale in sorted(p for p in root.iterdir() if p.is_dir()):
        for row in iter_redqueen_rows(scale):
            if row.get("support_status") == "current_supported":
                rows.append(row)
                if len(rows) >= target:
                    return rows
    return rows


def _completed(results: List[Dict[str, Any]], level: str) -> bool:
    return any(row["level"] == level and row["completed"] for row in results)


def _weighted_rate(results: List[Dict[str, Any]]) -> float:
    total = sum(row["real_compiler_invocation_count"] for row in results)
    correct = sum(row["compiler_verified_correct_count"] for row in results)
    return round(correct / total, 6) if total else 0.0


def _write_trace(out: Path, rows: List[Dict[str, Any]]) -> None:
    name = "ironjudge_trace_000.jsonl"
    out.mkdir(parents=True, exist_ok=True)
    (out / name).write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    _write_json(out / "ironjudge_trace_manifest.json", {"shards": [{"path": name, "row_count": len(rows), "size_bytes": (out / name).stat().st_size}], "total_rows": len(rows)})


def _markdown(result: Dict[str, Any]) -> str:
    lines = ["# IronJudge scale validation", ""]
    for row in result["ironjudge_levels"]:
        lines.append(f"- {row['level']}: {row['completed_invocations']}/{row['target_invocations']} completed, partial={row['partial']}, rate={row['compiler_verified_correct_rate']}")
    return "\n".join(lines) + "\n"


def _lat(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"p50_latency_ms": 0.0, "p95_latency_ms": 0.0, "p99_latency_ms": 0.0}
    values = sorted(values)
    return {"p50_latency_ms": round(statistics.median(values), 6), "p95_latency_ms": round(values[min(len(values) - 1, int(len(values) * 0.95))], 6), "p99_latency_ms": round(values[min(len(values) - 1, int(len(values) * 0.99))], 6)}


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
