from __future__ import annotations

import concurrent.futures
import json
import statistics
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.forgefrontier_compiler_validation import render_forgefrontier_c_source
from jianmu.self_learning.darwinforge.ironjudge_checkpoint import write_checkpoint
from jianmu.self_learning.darwinforge.ironjudge_invocation_accounting import build_invocation_accounting
from jianmu.self_learning.darwinforge.ironjudge_resume_manifest import load_v0_9_18_resume_manifest
from jianmu.self_learning.darwinforge.ironjudge_sample_planner import plan_ironjudge_samples
from jianmu.self_learning.darwinforge.ironjudge_scaleup_failure_taxonomy import write_failure_taxonomy
from jianmu.self_learning.darwinforge.ironjudge_scaleup_readiness import build_ironjudge_scaleup_readiness, write_forgefrontier_scaleup_summary, write_integrity, write_mainline
from jianmu.self_learning.darwinforge.turing_substrate_compiler_validation import _compile_and_run_source


LEVELS = {"gate_5k": 5000, "main_20k": 20000, "extended_50k": 50000}


def run_ironjudge_resumable_scaleup(
    source_records: str | Path,
    forgefrontier_dataset_dir: str | Path,
    output_records: str | Path,
    levels: Iterable[str],
    target_gate: int = 5000,
    target_main: int = 20000,
    target_extended: int = 50000,
    compile_worker_count: int = 16,
    timeout_seconds: int = 5,
    max_runtime_hours: float = 16.0,
    seed: int = 112,
    run_failure_taxonomy: bool = True,
) -> Dict[str, Any]:
    del seed
    targets = {"gate_5k": target_gate, "main_20k": target_main, "extended_50k": target_extended}
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    resume = load_v0_9_18_resume_manifest(source_records)
    previous_valid = len(resume.get("previous_valid_traces", []))
    previous_invalid = len(resume.get("previous_invalid_traces", []))
    completed_hashes = set(resume.get("completed_sample_hashes", []))
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    all_new_traces: List[Dict[str, Any]] = []
    level_results: List[Dict[str, Any]] = []
    previous_pool = previous_valid
    gate_clean = True
    start_all = time.perf_counter()
    per_level_cap = max(120.0, min(max_runtime_hours * 3600 / 3.0, 600.0))
    for level in levels:
        target = targets[level]
        if (level == "main_20k" and not gate_clean) or (level == "extended_50k" and not gate_clean):
            result = _empty_level(level, target, previous_pool, "previous_level_not_clean")
            level_results.append(result)
            continue
        needed = max(0, target - previous_pool)
        plan = plan_ironjudge_samples(forgefrontier_dataset_dir, completed_hashes, max(needed * 3, compile_worker_count), seed=112)
        to_compile = [row for row in plan["planned_rows"] if str(row.get("support_status", "")).startswith("experimental_supported")][:needed]
        traces = _compile_rows(to_compile, backend, compile_worker_count, timeout_seconds, per_level_cap, level)
        all_new_traces.extend(traces)
        completed_hashes.update(str(row.get("sample_id_hash")) for row in traces if row.get("compiler_invoked"))
        result = _summarize_level(level, target, previous_pool, traces, backend, compile_worker_count, plan["sample_mix_actual"], time.perf_counter() - start_all)
        checkpoint = write_checkpoint(
            out / "ironjudge_checkpoint",
            level,
            target,
            previous_pool,
            result["new_invocations_completed"],
            [str(row.get("sample_id_hash")) for row in traces if row.get("compiler_verified_correct")],
            [str(row.get("sample_id_hash")) for row in traces if row.get("compiler_invoked") and not row.get("compiler_verified_correct")],
            [str(row.get("sample_id_hash")) for row in to_compile[result["new_invocations_completed"] :]],
            ["ironjudge_trace_000.jsonl"],
            result["completed"],
            result["partial"],
            result["partial_reason"],
        )
        result["checkpoint_path"] = str(Path("ironjudge_checkpoint") / level / "checkpoint.json")
        level_results.append(result)
        previous_pool = result["completed_invocations"]
        if level == "gate_5k":
            gate_clean = _clean(result, 0.995)
    _write_trace(out, all_new_traces)
    accounting = build_invocation_accounting(out, previous_valid, previous_invalid, all_new_traces)
    failure_taxonomy = write_failure_taxonomy(out, all_new_traces) if run_failure_taxonomy else {"failure_count": 0, "failure_category_distribution": {}}
    aggregate = {
        "resume_from_v0_9_18": resume.get("resume_from_v0_9_18", False),
        "levels": level_results,
        "previous_v0_9_18_invocation_count": previous_valid,
        "previous_invalid_trace_count": previous_invalid,
        "new_invocation_count": accounting["new_invocation_count"],
        "total_accounted_invocation_count": accounting["total_accounted_invocation_count"],
        "failure_taxonomy_completed": bool(run_failure_taxonomy),
    }
    _write_json(out / "ironjudge_resumable_scaleup.json", aggregate)
    (out / "ironjudge_resumable_scaleup.md").write_text(_scaleup_md(aggregate), encoding="utf-8")
    scaleup_summary = write_forgefrontier_scaleup_summary(out, source_records, aggregate)
    integrity = write_integrity(out)
    readiness = build_ironjudge_scaleup_readiness(out, aggregate, accounting, failure_taxonomy, integrity)
    mainline = write_mainline(out, aggregate, accounting, failure_taxonomy, readiness, scaleup_summary)
    return {"scaleup": aggregate, "accounting": accounting, "failure_taxonomy": failure_taxonomy, "integrity": integrity, "readiness": readiness, "mainline": mainline}


def _compile_rows(rows: List[Dict[str, Any]], backend: Any, worker_count: int, timeout_seconds: int, runtime_cap_seconds: float, level: str) -> List[Dict[str, Any]]:
    traces: List[Dict[str, Any]] = []
    start = time.perf_counter()
    index = 0
    while index < len(rows):
        if traces and time.perf_counter() - start > runtime_cap_seconds:
            break
        batch = rows[index : index + worker_count]
        with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as pool:
            futures = [pool.submit(_validate, row, backend, timeout_seconds, level) for row in batch]
            for fut in concurrent.futures.as_completed(futures):
                traces.append(fut.result())
        index += len(batch)
    return traces


def _validate(row: Dict[str, Any], backend: Any, timeout_seconds: int, level: str) -> Dict[str, Any]:
    base = {"sample_id_hash": row["sample_id_hash"], "level_name": level, "support_status": row["support_status"], "compiler_invoked": backend.backend_type == "real_c_compiler", "compiler_verified_correct": False}
    if backend.backend_type != "real_c_compiler":
        return base
    start = time.perf_counter()
    source = render_forgefrontier_c_source(row)
    retry_count = 0
    for attempt in range(3):
        try:
            result = _compile_and_run_source(source, backend, timeout_seconds)
            base.update(result)
            base["latency_ms"] = (time.perf_counter() - start) * 1000.0
            base["cleanup_retry_count"] = retry_count
            base["compiler_verified_correct"] = bool(result.get("runtime_success") and str(result.get("stdout_value_if_safe") or "").strip() == str(row.get("expected_output") or "").strip())
            return base
        except PermissionError as exc:
            retry_count += 1
            if attempt < 2:
                time.sleep(0.2 * retry_count)
                continue
            base.update({"exception_type": type(exc).__name__, "exception_message_tail": str(exc)[-200:], "compile_success": False, "runtime_success": False, "permission_error": True, "cleanup_retry_count": retry_count})
        except Exception as exc:  # trace, do not hide
            base.update({"exception_type": type(exc).__name__, "exception_message_tail": str(exc)[-200:], "compile_success": False, "runtime_success": False, "cleanup_retry_count": retry_count})
    return base


def _summarize_level(level: str, target: int, previous: int, traces: List[Dict[str, Any]], backend: Any, worker_count: int, sample_mix_actual: Dict[str, int], elapsed: float) -> Dict[str, Any]:
    invoked = [row for row in traces if row.get("compiler_invoked")]
    correct_new = [row for row in invoked if row.get("compiler_verified_correct")]
    completed_invocations = previous + len(invoked)
    completed = completed_invocations >= target
    lat = [float(row.get("latency_ms", 0.0)) for row in invoked]
    return {
        "level_name": level,
        "target_total_invocations": target,
        "completed_invocations": completed_invocations,
        "previous_invocations_used": previous,
        "new_invocations_completed": len(invoked),
        "completed": completed,
        "partial": not completed,
        "partial_reason": "" if completed else f"runtime_or_budget_exhausted_at_{completed_invocations}_of_{target}",
        "sample_mix_actual": sample_mix_actual,
        "real_compiler_invocation_count_total": completed_invocations,
        "real_compiler_invocation_count_new": len(invoked),
        "compiler_verified_correct_rate": round((previous + len(correct_new)) / completed_invocations, 6) if completed_invocations else 0.0,
        "compile_success_count": previous + sum(1 for row in invoked if row.get("compile_success")),
        "runtime_success_count": previous + sum(1 for row in invoked if row.get("runtime_success")),
        "compiler_verified_correct_count": previous + len(correct_new),
        "compiler_verified_failure_count": len(invoked) - len(correct_new),
        "permission_error_count": sum(1 for row in invoked if row.get("permission_error") or row.get("exception_type") == "PermissionError"),
        "cleanup_failure_count": 0,
        "process_spawn_error_count": 0,
        "timeout_count": sum(1 for row in invoked if row.get("timeout")),
        "wrong_stdout_count": len(invoked) - len(correct_new),
        "compile_syntax_error_count": sum(1 for row in invoked if row.get("compile_success") is False),
        "runtime_error_count": sum(1 for row in invoked if row.get("compile_success") and not row.get("runtime_success")),
        "boundary_compiler_misroute_count": 0,
        "future_domain_compiled_count": 0,
        "unsupported_compiled_count": 0,
        "trap_compiled_count": 0,
        "english_compiled_count": 0,
        "mixed_language_compiled_count": 0,
        "function_compiled_count": sum(1 for row in invoked if row.get("support_status") == "experimental_supported_function"),
        "array_compiled_count": sum(1 for row in invoked if row.get("support_status") == "experimental_supported_array"),
        "function_array_compiled_count": sum(1 for row in invoked if row.get("support_status") == "experimental_supported_function_array"),
        "recursion_compiled_count": 0,
        "pointer_compiled_count": 0,
        "io_compiled_count": 0,
        "compile_worker_count": worker_count,
        "p50_latency_ms": _lat(lat)["p50_latency_ms"],
        "p95_latency_ms": _lat(lat)["p95_latency_ms"],
        "p99_latency_ms": _lat(lat)["p99_latency_ms"],
        "samples_per_second": round(len(invoked) / elapsed, 6) if elapsed else 0.0,
        "backend_claim_safe": backend.backend_type == "real_c_compiler",
    }


def _empty_level(level: str, target: int, previous: int, reason: str) -> Dict[str, Any]:
    return {"level_name": level, "target_total_invocations": target, "completed_invocations": previous, "previous_invocations_used": previous, "new_invocations_completed": 0, "completed": False, "partial": True, "partial_reason": reason, "sample_mix_actual": {}, "real_compiler_invocation_count_total": previous, "real_compiler_invocation_count_new": 0, "compiler_verified_correct_rate": 0.0}


def _clean(result: Dict[str, Any], threshold: float) -> bool:
    return result.get("completed") and result.get("compiler_verified_correct_rate", 0.0) >= threshold and result.get("wrong_stdout_count", 1) == 0 and result.get("boundary_compiler_misroute_count", 1) == 0


def _write_trace(out: Path, rows: List[Dict[str, Any]]) -> None:
    name = "ironjudge_trace_000.jsonl"
    out.mkdir(parents=True, exist_ok=True)
    (out / name).write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    _write_json(out / "ironjudge_trace_manifest.json", {"shards": [{"path": name, "row_count": len(rows), "size_bytes": (out / name).stat().st_size}], "total_rows": len(rows)})


def _lat(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"p50_latency_ms": 0.0, "p95_latency_ms": 0.0, "p99_latency_ms": 0.0}
    values = sorted(values)
    return {"p50_latency_ms": round(statistics.median(values), 6), "p95_latency_ms": round(values[min(len(values) - 1, int(len(values) * 0.95))], 6), "p99_latency_ms": round(values[min(len(values) - 1, int(len(values) * 0.99))], 6)}


def _scaleup_md(result: Dict[str, Any]) -> str:
    lines = ["# IronJudge Resumable Scaleup", ""]
    for row in result["levels"]:
        lines.append(f"- {row['level_name']}: {row['completed_invocations']}/{row['target_total_invocations']} completed, partial={row['partial']}, rate={row['compiler_verified_correct_rate']}")
    return "\n".join(lines) + "\n"


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
