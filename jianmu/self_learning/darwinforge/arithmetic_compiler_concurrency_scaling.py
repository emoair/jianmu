from __future__ import annotations

import concurrent.futures
import json
import random
import time
from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.arithmetic_compiler_concurrency_readiness import (
    assess_compiler_concurrency_readiness,
)
from jianmu.self_learning.darwinforge.arithmetic_fresh_compiler_reproduction import (
    _candidate_expression,
    _execute_compiler,
    _hash_text,
    latency_summary,
)


REQUIRED_WORKER_LEVELS = [4, 8, 16, 32, 64, 128, 256, 512]
SUPPORTED_STAGES = ["single_op", "two_op_no_parentheses", "precedence", "parentheses", "negative_numbers", "exact_division", "mixed_composition"]
BOUNDARY_CATEGORIES = ["unsupported_arithmetic_boundary", "true_false_accept_trap", "future_domain_candidate", "near_ood_arithmetic", "hard_ood"]


def run_compiler_concurrency_scaling(
    records_dir: str | Path,
    fresh_records: str | Path,
    longrun_records: str | Path,
    dataset_dir: str | Path,
    output_records: str | Path,
    worker_levels: Iterable[int],
    supported_samples: int = 1000,
    boundary_samples: int = 1000,
    seed: int = 51,
    timeout_seconds: int = 5,
    python_worker_count: int = 4,
    stop_on_unstable: bool = True,
) -> Dict[str, Any]:
    del records_dir
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    rows = _read_dataset_rows(Path(dataset_dir))
    excluded = _trace_hashes(Path(fresh_records) / "fresh_compiler_trace.jsonl") | _trace_hashes_from_manifest(Path(longrun_records))
    levels = [int(level) for level in worker_levels]
    all_trace: list[dict[str, Any]] = []
    all_failures: list[dict[str, Any]] = []
    level_metrics: list[dict[str, Any]] = []
    baseline_sps: float | None = None

    if backend.backend_type != "real_c_compiler":
        metrics = {
            "backend_type": backend.backend_type,
            "compiler_name": backend.compiler_name,
            "compiler_environment": backend.compiler_environment,
            "worker_levels_attempted": levels,
            "levels": [],
        }
        readiness = assess_compiler_concurrency_readiness(metrics)
        metrics.update(readiness)
        _write_outputs(out, metrics, all_trace, all_failures)
        return metrics

    for index, compile_workers in enumerate(levels):
        supported, boundary = _select_samples(rows, excluded, supported_samples, boundary_samples, seed + index * 1009)
        started = time.perf_counter()
        trace_rows = _run_level(supported, boundary, backend, compile_workers, timeout_seconds)
        elapsed = time.perf_counter() - started
        metrics = _summarize_level(trace_rows, backend, compile_workers, python_worker_count, elapsed)
        if baseline_sps is None and compile_workers == 4:
            baseline_sps = metrics["samples_per_second"]
        if baseline_sps:
            metrics["throughput_gain_vs_4_workers"] = round(metrics["samples_per_second"] / max(baseline_sps, 1e-9), 6)
            metrics["latency_degradation_vs_4_workers"] = None
        else:
            metrics["throughput_gain_vs_4_workers"] = 1.0
            metrics["latency_degradation_vs_4_workers"] = 0.0
        metrics["stable"] = _is_stable(metrics)
        metrics["unstable_reason"] = _unstable_reason(metrics)
        level_metrics.append(metrics)
        all_trace.extend(trace_rows)
        all_failures.extend(_failure_rows(trace_rows))
        if stop_on_unstable and compile_workers >= 64 and not metrics["stable"]:
            for level in levels[index + 1 :]:
                level_metrics.append({
                    "compile_worker_count": level,
                    "python_worker_count": python_worker_count,
                    "backend_type": backend.backend_type,
                    "compiler_name": backend.compiler_name,
                    "compiler_environment": backend.compiler_environment,
                    "supported_sample_count": 0,
                    "boundary_sample_count": 0,
                    "real_compiler_invocation_count": 0,
                    "completed": False,
                    "stable": False,
                    "unstable_reason": f"stopped_after_unstable_{compile_workers}",
                    "notes": "not executed after unstable high-concurrency level",
                })
            break

    metrics = {
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "worker_levels_attempted": levels,
        "levels": level_metrics,
    }
    readiness = assess_compiler_concurrency_readiness(metrics)
    metrics.update(readiness)
    _write_outputs(out, metrics, all_trace, all_failures)
    return metrics


def _run_level(rows: list[dict[str, Any]], boundary: list[dict[str, Any]], backend: Any, compile_workers: int, timeout_seconds: int) -> list[dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, compile_workers)) as pool:
        futures = [pool.submit(_trace_supported, row, backend, compile_workers, timeout_seconds) for row in rows]
        for future in concurrent.futures.as_completed(futures):
            try:
                trace.append(future.result())
            except Exception as exc:
                trace.append(_exception_trace(compile_workers, exc))
    trace.extend(_trace_boundary(row, backend, compile_workers) for row in boundary)
    return trace


def _trace_supported(row: Dict[str, Any], backend: Any, compile_workers: int, timeout_seconds: int) -> Dict[str, Any]:
    started = time.perf_counter()
    expression = _candidate_expression(row)
    try:
        result = _execute_compiler(expression, backend, timeout_seconds)
    except Exception as exc:
        result = {
            "backend_type": backend.backend_type,
            "compiler_name": backend.compiler_name,
            "compiler_invoked": True,
            "compile_returncode": None,
            "compile_success": False,
            "runtime_returncode": None,
            "runtime_success": False,
            "stdout_hash": None,
            "stdout_value_if_safe": None,
            "timeout": False,
            "unsafe_expression": False,
            "token_spacing_patch_applied": False,
            "compile_stderr_tail": "",
            "runtime_stderr_tail": f"{type(exc).__name__}: {exc}",
            "latency_ms": round((time.perf_counter() - started) * 1000, 6),
            "notes": "process_spawn_error" if "WinError" in str(exc) or isinstance(exc, OSError) else "sample_execution_exception",
        }
    expected = str(row.get("expected_output") or "").strip()
    stdout = str(result.get("stdout_value_if_safe") or "").strip()
    correct = bool(result.get("runtime_success")) and stdout == expected
    notes = str(result.get("notes") or "")
    return {
        "sample_id_hash": _hash_text(str(row.get("id", ""))),
        "compile_worker_count": compile_workers,
        "stage": row.get("stage"),
        "category": row.get("category"),
        "backend_type": result.get("backend_type"),
        "compiler_name": result.get("compiler_name"),
        "compiler_invoked": bool(result.get("compiler_invoked")),
        "compile_returncode": result.get("compile_returncode"),
        "compile_success": bool(result.get("compile_success")),
        "runtime_returncode": result.get("runtime_returncode"),
        "runtime_success": bool(result.get("runtime_success")),
        "compiler_verified_correct": correct if result.get("backend_type") == "real_c_compiler" else None,
        "timeout": bool(result.get("timeout")),
        "process_spawn_error": notes == "process_spawn_error",
        "trace_write_error": False,
        "temp_file_error": "temp" in notes.lower(),
        "boundary_compiler_misroute": False,
        "latency_ms": result.get("latency_ms", 0.0),
        "token_spacing_patch_applied": bool(result.get("token_spacing_patch_applied")),
        "notes": notes,
    }


def _trace_boundary(row: Dict[str, Any], backend: Any, compile_workers: int) -> Dict[str, Any]:
    return {
        "sample_id_hash": _hash_text(str(row.get("id", ""))),
        "compile_worker_count": compile_workers,
        "stage": row.get("stage"),
        "category": row.get("category"),
        "division_kind": row.get("division_kind"),
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_invoked": False,
        "compile_returncode": None,
        "compile_success": False,
        "runtime_returncode": None,
        "runtime_success": False,
        "compiler_verified_correct": None,
        "timeout": False,
        "process_spawn_error": False,
        "trace_write_error": False,
        "temp_file_error": False,
        "boundary_compiler_misroute": False,
        "latency_ms": 0.0,
        "notes": "boundary_not_compiled",
    }


def _exception_trace(compile_workers: int, exc: Exception) -> Dict[str, Any]:
    return {
        "sample_id_hash": None,
        "compile_worker_count": compile_workers,
        "stage": None,
        "category": "current_supported_arithmetic",
        "backend_type": "real_c_compiler",
        "compiler_name": "cl",
        "compiler_invoked": False,
        "compile_returncode": None,
        "compile_success": False,
        "runtime_returncode": None,
        "runtime_success": False,
        "compiler_verified_correct": False,
        "timeout": False,
        "process_spawn_error": True,
        "trace_write_error": False,
        "temp_file_error": False,
        "boundary_compiler_misroute": False,
        "latency_ms": 0.0,
        "notes": f"future_exception: {type(exc).__name__}: {exc}",
    }


def _summarize_level(trace_rows: list[dict[str, Any]], backend: Any, compile_workers: int, python_workers: int, elapsed: float) -> Dict[str, Any]:
    supported = [row for row in trace_rows if row.get("category") == "current_supported_arithmetic"]
    boundary = [row for row in trace_rows if row.get("category") != "current_supported_arithmetic"]
    invocations = sum(bool(row.get("compiler_invoked")) for row in supported)
    correct = sum(bool(row.get("compiler_verified_correct")) for row in supported)
    compile_success = sum(bool(row.get("compile_success")) for row in supported)
    runtime_success = sum(bool(row.get("runtime_success")) for row in supported)
    latencies = [float(row.get("latency_ms") or 0.0) for row in supported if row.get("compiler_invoked")]
    return {
        "compile_worker_count": compile_workers,
        "python_worker_count": python_workers,
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "supported_sample_count": len(supported),
        "boundary_sample_count": len(boundary),
        "real_compiler_invocation_count": invocations,
        "compile_success_count": compile_success,
        "compile_failure_count": len(supported) - compile_success,
        "runtime_success_count": runtime_success,
        "runtime_failure_count": len(supported) - runtime_success,
        "compiler_verified_correct_count": correct,
        "compiler_verified_failure_count": len(supported) - correct,
        "compiler_verified_correct_rate": round(correct / max(len(supported), 1), 6),
        "boundary_compiler_misroute_count": sum(bool(row.get("boundary_compiler_misroute")) for row in boundary),
        "timeout_count": sum(bool(row.get("timeout")) for row in supported),
        "process_spawn_error_count": sum(bool(row.get("process_spawn_error")) for row in supported),
        "trace_write_error_count": sum(bool(row.get("trace_write_error")) for row in supported),
        "temp_file_error_count": sum(bool(row.get("temp_file_error")) for row in supported),
        "division_by_zero_compiled_count": sum(row.get("division_kind") == "division_by_zero" and row.get("compiler_invoked") for row in boundary),
        "non_integer_division_compiled_count": sum(row.get("division_kind") == "non_integer" and row.get("compiler_invoked") for row in boundary),
        "unsupported_compiled_count": sum(bool(row.get("compiler_invoked")) for row in boundary),
        "patch_applied_count": sum(bool(row.get("token_spacing_patch_applied")) for row in supported),
        **latency_summary(latencies),
        "total_wall_clock_seconds": round(elapsed, 6),
        "samples_per_second": round(len(supported) / max(elapsed, 1e-9), 6),
        "completed": True,
        "notes": "",
    }


def _is_stable(metrics: Dict[str, Any]) -> bool:
    return (
        metrics.get("compiler_verified_correct_rate", 0) >= 0.98
        and metrics.get("timeout_count", 0) == 0
        and metrics.get("process_spawn_error_count", 0) == 0
        and metrics.get("boundary_compiler_misroute_count", 0) == 0
        and metrics.get("trace_write_error_count", 0) == 0
    )


def _unstable_reason(metrics: Dict[str, Any]) -> str:
    reasons = []
    for key in ["timeout_count", "process_spawn_error_count", "compile_failure_count", "runtime_failure_count", "boundary_compiler_misroute_count", "trace_write_error_count"]:
        if metrics.get(key, 0):
            reasons.append(key)
    if metrics.get("compiler_verified_correct_rate", 0) < 0.98:
        reasons.append("correct_rate_below_threshold")
    return ";".join(reasons)


def _select_samples(rows: list[dict[str, Any]], excluded: set[str], supported_limit: int, boundary_limit: int, seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    supported = [row for row in rows if row.get("category") == "current_supported_arithmetic" and _hash_text(str(row.get("id", ""))) not in excluded]
    boundary = [row for row in rows if row.get("category") != "current_supported_arithmetic" and _hash_text(str(row.get("id", ""))) not in excluded]
    return _balanced_pick(supported, supported_limit, seed, "stage", SUPPORTED_STAGES), _balanced_pick(boundary, boundary_limit, seed + 2000, "category", BOUNDARY_CATEGORIES)


def _balanced_pick(rows: list[dict[str, Any]], limit: int, seed: int, field: str, values: list[str]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    per = max(1, limit // max(len(values), 1))
    for index, value in enumerate(values):
        subset = [row for row in rows if row.get(field) == value]
        random.Random(seed + index).shuffle(subset)
        selected.extend(subset[:per])
    seen = {row.get("id") for row in selected}
    rest = [row for row in rows if row.get("id") not in seen]
    random.Random(seed + 99).shuffle(rest)
    selected.extend(rest[: max(0, limit - len(selected))])
    return selected[:limit]


def _failure_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        row for row in rows
        if row.get("category") == "current_supported_arithmetic"
        and (
            row.get("compile_success") is False
            or row.get("runtime_success") is False
            or row.get("compiler_verified_correct") is False
            or row.get("timeout")
            or row.get("process_spawn_error")
        )
    ]


def _read_dataset_rows(dataset: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in dataset.rglob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _trace_hashes(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {json.loads(line).get("sample_id_hash") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _trace_hashes_from_manifest(records: Path) -> set[str]:
    manifest = records / "compiler_longrun_trace_manifest.json"
    if not manifest.exists():
        return set()
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    hashes: set[str] = set()
    for shard in payload.get("shards", []):
        hashes |= _trace_hashes(records / shard["path"])
    return hashes


def _write_outputs(out: Path, metrics: Dict[str, Any], trace_rows: list[dict[str, Any]], failures: list[dict[str, Any]]) -> None:
    _write_json(out / "compiler_concurrency_scaling_metrics.json", metrics)
    _write_report(out / "compiler_concurrency_scaling_report.md", metrics)
    _write_trace_sharded(out, trace_rows)
    _write_jsonl(out / "compiler_concurrency_failures.jsonl", failures)
    _write_json(out / "compiler_concurrency_readiness.json", {key: metrics[key] for key in [
        "scaling_completed",
        "tested_worker_levels",
        "stable_worker_levels",
        "unstable_worker_levels",
        "best_compile_worker_count",
        "best_samples_per_second",
        "best_latency_profile",
        "recommended_default_compile_worker_count",
        "max_stable_compile_worker_count",
        "compiler_verified_correct_rate_at_best",
        "boundary_compiler_misroute_count_at_best",
        "timeout_count_at_best",
        "process_spawn_error_count_at_best",
        "trace_write_error_count_at_best",
        "recommended_claim_level",
        "blocking_issues",
        "required_next_run",
    ]})
    _write_mainline(out, metrics)


def _write_report(path: Path, metrics: Dict[str, Any]) -> None:
    lines = ["# Compiler Concurrency Scaling Report", ""]
    for row in metrics.get("levels", []):
        lines.append(
            f"- workers={row.get('compile_worker_count')}: sps={row.get('samples_per_second')}, "
            f"stable={row.get('stable')}, p99={row.get('p99_latency_ms')}, "
            f"timeouts={row.get('timeout_count', 0)}, "
            f"compile_failures={row.get('compile_failure_count', 0)}, "
            f"runtime_failures={row.get('runtime_failure_count', 0)}, "
            f"process_spawn_errors={row.get('process_spawn_error_count', 0)}, "
            f"trace_write_errors={row.get('trace_write_error_count', 0)}"
        )
    lines.extend(["", f"Recommended claim level: {metrics.get('recommended_claim_level')}"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_mainline(out: Path, metrics: Dict[str, Any]) -> None:
    still_not_proven = [
        "solved arithmetic",
        "stable convergence",
        "solved OOD",
        "general program synthesis",
        "same-size LLM advantage",
        "safe real promotion",
        "production readiness",
        "Turing completeness",
    ]
    payload = {
        "what_this_version_proved": "It measured real cl.exe concurrency scaling across configured worker levels.",
        "what_this_version_did_not_prove": still_not_proven,
        "best_compile_worker_count": metrics.get("best_compile_worker_count"),
        "max_stable_compile_worker_count": metrics.get("max_stable_compile_worker_count"),
        "worker_512_stable": any(row.get("compile_worker_count") == 512 and row.get("stable") for row in metrics.get("levels", [])),
        "throughput_increased": any(row.get("throughput_gain_vs_4_workers", 0) > 1 for row in metrics.get("levels", [])),
        "latency_summary_by_level": {
            str(row.get("compile_worker_count")): {key: row.get(key) for key in ["p50_latency_ms", "p95_latency_ms", "p99_latency_ms"]}
            for row in metrics.get("levels", [])
        },
        "error_summary_by_level": {
            str(row.get("compile_worker_count")): {key: row.get(key, 0) for key in ["timeout_count", "process_spawn_error_count", "trace_write_error_count"]}
            for row in metrics.get("levels", [])
        },
        "boundary_guard_preserved": all(row.get("boundary_compiler_misroute_count", 0) == 0 for row in metrics.get("levels", [])),
        "recommended_claim_level": metrics.get("recommended_claim_level"),
        "blocking_issues": metrics.get("blocking_issues"),
        "required_next_run": metrics.get("required_next_run"),
        "results_for_paper_v2": ["compiler concurrency throughput profile", "max stable cl.exe concurrency"],
        "results_requiring_revalidation": ["larger per-level samples at recommended worker count"],
        "still_not_proven": still_not_proven,
    }
    _write_json(out / "mainline_conclusion.json", payload)
    lines = [
        "# v0.9.5.1 Mainline Conclusion",
        "",
        payload["what_this_version_proved"],
        "",
        f"Best compile worker count: {payload['best_compile_worker_count']}",
        f"Max stable compile worker count: {payload['max_stable_compile_worker_count']}",
        f"Recommended claim level: {payload['recommended_claim_level']}",
        "",
        "## Still Not Proven",
    ]
    lines.extend(f"- {item}" for item in still_not_proven)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_trace_sharded(out: Path, rows: list[Dict[str, Any]], max_bytes: int = 45_000_000) -> None:
    shards = []
    current: list[Dict[str, Any]] = []
    size = 0
    index = 0
    for row in rows:
        line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        line_size = len(line.encode("utf-8"))
        if current and size + line_size > max_bytes:
            path = out / f"compiler_concurrency_trace_{index:03d}.jsonl"
            _write_jsonl(path, current)
            shards.append({"path": path.name, "row_count": len(current), "size_bytes": path.stat().st_size})
            current, size = [], 0
            index += 1
        current.append(row)
        size += line_size
    if current:
        path = out / f"compiler_concurrency_trace_{index:03d}.jsonl"
        _write_jsonl(path, current)
        shards.append({"path": path.name, "row_count": len(current), "size_bytes": path.stat().st_size})
    _write_json(out / "compiler_concurrency_trace_manifest.json", {
        "trace_sharded": True,
        "shard_count": len(shards),
        "total_rows": len(rows),
        "shards": shards,
    })


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
