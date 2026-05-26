from __future__ import annotations

import concurrent.futures
import json
import statistics
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.bounded_substrate_compiler_temp_manager import validate_sample_with_temp_manager
from jianmu.self_learning.darwinforge.bounded_substrate_permission_failure_taxonomy import classify_failure_row


def replay_permission_failures(
    source_records: str | Path,
    dataset_dir: str | Path,
    output_records: str | Path,
    compile_worker_count: int = 16,
    timeout_seconds: int = 5,
) -> Dict[str, Any]:
    source = Path(source_records)
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    failures = _read_jsonl(source / "compiler_validation_failures.jsonl")
    rows = _load_rows_by_hash(Path(dataset_dir) / "large")
    replay_inputs = []
    for failure in failures:
        row = rows.get(failure.get("sample_id_hash"))
        if row:
            replay_inputs.append((failure, row))
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    trace: List[Dict[str, Any]] = []
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=compile_worker_count) as pool:
        futs = []
        for index, (failure, row) in enumerate(replay_inputs):
            futs.append(pool.submit(_replay_one, failure, row, out, index % compile_worker_count, timeout_seconds, backend))
        for fut in concurrent.futures.as_completed(futs):
            trace.append(fut.result())
    _write_jsonl(out / "permission_replay_trace.jsonl", trace)
    _write_jsonl(out / "patched_replay_trace.jsonl", trace)
    metrics = _summarize_patched(failures, trace, time.perf_counter() - started)
    _write_json(out / "patched_replay_metrics.json", metrics)
    return metrics


def run_independent_validation(
    dataset_dir: str | Path,
    output_records: str | Path,
    supported_samples: int = 2000,
    boundary_samples: int = 2000,
    compile_worker_count: int = 16,
    seed: int = 60,
    timeout_seconds: int = 5,
) -> Dict[str, Any]:
    out = Path(output_records)
    rows = list(_iter_rows(Path(dataset_dir) / "large"))
    supported = [row for row in rows if row.get("category") == "current_supported_turing_substrate"]
    boundary = [row for row in rows if row.get("category") != "current_supported_turing_substrate"]
    supported = _sample(supported, supported_samples, seed)
    boundary = _sample(boundary, boundary_samples, seed + 500)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    trace: List[Dict[str, Any]] = []
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=compile_worker_count) as pool:
        futs = [pool.submit(validate_sample_with_temp_manager, row, out, "independent", idx % compile_worker_count, timeout_seconds, backend) for idx, row in enumerate(supported)]
        for fut in concurrent.futures.as_completed(futs):
            trace.append(fut.result())
    for row in boundary:
        trace.append({
            "sample_id_hash": _hash(row.get("id", "")),
            "category": row.get("category"),
            "stage": row.get("stage"),
            "compiler_invoked": False,
            "compiler_verified_correct": False,
            "boundary_compiler_misroute": False,
            "notes": "boundary_not_compiled",
        })
    _write_sharded_trace(out, trace)
    metrics = _summarize_independent(trace, supported, boundary, time.perf_counter() - started, backend, compile_worker_count)
    _write_json(out / "independent_validation_metrics.json", metrics)
    return metrics


def _replay_one(failure: Dict[str, Any], row: Dict[str, Any], out: Path, worker_id: int, timeout_seconds: int, backend: Any) -> Dict[str, Any]:
    result = validate_sample_with_temp_manager(row, out, "patched_replay", worker_id, timeout_seconds, backend)
    result.update({
        "original_failure_type": classify_failure_row(failure),
        "replay_failure_type": _failure_type(result),
        "replay_success": result.get("compiler_verified_correct", False),
    })
    return result


def _summarize_patched(original_failures: List[Dict[str, Any]], trace: List[Dict[str, Any]], elapsed: float) -> Dict[str, Any]:
    verified = sum(1 for row in trace if row.get("compiler_verified_correct"))
    compile_success = sum(1 for row in trace if row.get("compile_success"))
    runtime_success = sum(1 for row in trace if row.get("runtime_success"))
    permission_errors = sum(1 for row in trace if str(row.get("exception_type")) == "PermissionError" or str(row.get("permission_error_stage", "")).startswith("permission_"))
    cleanup_failures = sum(1 for row in trace if row.get("cleanup_failure_count", 0))
    return {
        "original_failure_count": len(original_failures),
        "patched_replay_sample_count": len(trace),
        "patched_compile_success_count": compile_success,
        "patched_runtime_success_count": runtime_success,
        "patched_compiler_verified_correct_count": verified,
        "patched_compiler_verified_failure_count": len(trace) - verified,
        "patched_compiler_verified_correct_rate": round(verified / len(trace), 6) if trace else 0.0,
        "patched_permission_error_count": permission_errors,
        "patched_cleanup_failure_count": cleanup_failures,
        "patched_remaining_failure_count": len(trace) - verified,
        "patched_delta_vs_original": verified,
        "original_result_preserved": True,
        "this_is_failure_replay_not_independent_full_rerun": True,
        "total_wall_clock_seconds": round(elapsed, 6),
    }


def _summarize_independent(trace: List[Dict[str, Any]], supported: List[Dict[str, Any]], boundary: List[Dict[str, Any]], elapsed: float, backend: Any, compile_worker_count: int) -> Dict[str, Any]:
    supported_trace = [row for row in trace if row.get("category") == "current_supported_turing_substrate"]
    verified = sum(1 for row in supported_trace if row.get("compiler_verified_correct"))
    latencies = sorted(row.get("latency_ms", 0.0) for row in supported_trace if row.get("compiler_invoked"))
    return {
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "compile_worker_count": compile_worker_count,
        "supported_sample_count": len(supported),
        "boundary_sample_count": len(boundary),
        "real_compiler_invocation_count": sum(1 for row in supported_trace if row.get("compiler_invoked")),
        "compile_success_count": sum(1 for row in supported_trace if row.get("compile_success")),
        "compile_failure_count": len(supported_trace) - sum(1 for row in supported_trace if row.get("compile_success")),
        "runtime_success_count": sum(1 for row in supported_trace if row.get("runtime_success")),
        "runtime_failure_count": len(supported_trace) - sum(1 for row in supported_trace if row.get("runtime_success")),
        "compiler_verified_correct_count": verified,
        "compiler_verified_failure_count": len(supported_trace) - verified,
        "compiler_verified_correct_rate": round(verified / len(supported_trace), 6) if supported_trace else 0.0,
        "permission_error_count": sum(1 for row in supported_trace if row.get("exception_type") == "PermissionError" or str(row.get("permission_error_stage", "")).startswith("permission_")),
        "cleanup_failure_count": sum(1 for row in supported_trace if row.get("cleanup_failure_count", 0)),
        "boundary_compiler_misroute_count": sum(1 for row in trace if row.get("boundary_compiler_misroute")),
        "timeout_count": sum(1 for row in supported_trace if row.get("timeout")),
        "p50_latency_ms": round(statistics.median(latencies), 6) if latencies else 0.0,
        "p95_latency_ms": latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))] if latencies else 0.0,
        "p99_latency_ms": latencies[min(len(latencies) - 1, int(len(latencies) * 0.99))] if latencies else 0.0,
        "samples_per_second": round(len(supported_trace) / elapsed, 6) if elapsed > 0 else 0.0,
        "backend_claim_safe": backend.backend_type == "real_c_compiler",
    }


def _failure_type(row: Dict[str, Any]) -> str:
    if row.get("compiler_verified_correct"):
        return "none"
    if row.get("exception_type") == "PermissionError":
        return row.get("permission_error_stage", "permission_unknown")
    if row.get("timeout"):
        return "runtime_timeout"
    if not row.get("compile_success"):
        return "compile_syntax_error"
    if not row.get("runtime_success"):
        return "runtime_error"
    return "wrong_output"


def _load_rows_by_hash(scale_dir: Path) -> Dict[str, Dict[str, Any]]:
    return {_hash(row.get("id", "")): row for row in _iter_rows(scale_dir)}


def _iter_rows(scale_dir: Path) -> Iterable[Dict[str, Any]]:
    for split in ["train", "eval", "test", "heldout"]:
        for path in sorted((scale_dir / split).glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    yield json.loads(line)


def _sample(rows: List[Dict[str, Any]], count: int, seed: int) -> List[Dict[str, Any]]:
    rows = list(rows)
    rows.sort(key=lambda row: _hash(row.get("id", "") + str(seed)))
    return rows[: min(count, len(rows))]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_sharded_trace(out: Path, trace: List[Dict[str, Any]]) -> None:
    path = out / "independent_validation_trace_000.jsonl"
    _write_jsonl(path, trace)
    _write_json(out / "independent_validation_trace_manifest.json", {"trace_sharded": True, "shard_count": 1, "total_rows": len(trace), "shards": [{"path": path.name, "row_count": len(trace), "size_bytes": path.stat().st_size}]})


def _hash(value: Any) -> str:
    import hashlib
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]
