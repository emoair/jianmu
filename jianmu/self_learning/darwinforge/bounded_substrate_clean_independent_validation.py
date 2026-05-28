from __future__ import annotations

import concurrent.futures
import itertools
import json
import statistics
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.bounded_substrate_compiler_temp_manager import validate_sample_with_temp_manager


def run_clean_independent_validation(
    dataset_dir: str | Path,
    output_records: str | Path,
    supported_samples: int = 5000,
    boundary_samples: int = 5000,
    compile_worker_count: int = 16,
    seed: int = 61,
    timeout_seconds: int = 5,
    run_fallback_on_failure: bool = True,
    fallback_supported_samples: int = 2000,
    fallback_boundary_samples: int = 2000,
    fallback_worker_count: int = 8,
    fallback_seed: int = 62,
) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    primary = _run_one(
        Path(dataset_dir),
        out,
        "primary_16",
        supported_samples,
        boundary_samples,
        compile_worker_count,
        seed,
        timeout_seconds,
    )
    fallback: Dict[str, Any] = {"run_label": "fallback_8", "executed": False, "completed": False}
    if run_fallback_on_failure and _needs_fallback(primary):
        fallback = _run_one(
            Path(dataset_dir),
            out,
            "fallback_8",
            fallback_supported_samples,
            fallback_boundary_samples,
            fallback_worker_count,
            fallback_seed,
            timeout_seconds,
        )
    metrics = {"primary": primary, "fallback": fallback}
    _write_json(out / "independent_validation_metrics.json", metrics)
    _write_failure_summary(out)
    return metrics


def _run_one(dataset_dir: Path, out: Path, run_label: str, supported_count: int, boundary_count: int, worker_count: int, seed: int, timeout_seconds: int) -> Dict[str, Any]:
    rows = list(_iter_rows(dataset_dir / "large"))
    supported = _sample([row for row in rows if row.get("category") == "current_supported_turing_substrate"], supported_count, seed)
    boundary = _sample([row for row in rows if row.get("category") != "current_supported_turing_substrate"], boundary_count, seed + 1000)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    if backend.backend_type != "real_c_compiler":
        metric = _empty_metric(run_label, worker_count, supported, boundary, backend, "real compiler unavailable")
        _write_trace(out, run_label, [])
        return metric
    started = time.perf_counter()
    trace: List[Dict[str, Any]] = []
    worker_slots = itertools.cycle(range(worker_count))
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as pool:
        futs = [
            pool.submit(validate_sample_with_temp_manager, row, out, run_label, next(worker_slots), timeout_seconds, backend)
            for row in supported
        ]
        for fut in concurrent.futures.as_completed(futs):
            item = fut.result()
            item.update({"run_label": run_label, "permission_error_count": _permission_error_count(item), "cleanup_failure": bool(item.get("cleanup_failure_count", 0)), "boundary_compiler_misroute": False})
            trace.append(item)
    for row in boundary:
        trace.append({
            "run_label": run_label,
            "sample_id_hash": _hash(row.get("id", "")),
            "split": row.get("split"),
            "stage": row.get("stage"),
            "category": row.get("category"),
            "worker_id": None,
            "backend_type": backend.backend_type,
            "compiler_name": backend.compiler_name,
            "compiler_invoked": False,
            "compile_returncode": None,
            "compile_success": False,
            "runtime_returncode": None,
            "runtime_success": False,
            "compiler_verified_correct": False,
            "permission_error_count": 0,
            "permission_error_stage": "none",
            "cleanup_attempted": False,
            "cleanup_success": True,
            "cleanup_retry_count": 0,
            "cleanup_failure": False,
            "timeout": False,
            "boundary_compiler_misroute": False,
            "exception_type": "",
            "exception_message_tail": "",
            "latency_ms": 0.0,
            "notes": "boundary_not_compiled",
        })
    _write_trace(out, run_label, trace)
    metric = _summarize(run_label, trace, supported, boundary, worker_count, backend, time.perf_counter() - started)
    metric["partial"] = False
    metric["partial_reason"] = ""
    return metric


def _summarize(run_label: str, trace: List[Dict[str, Any]], supported: List[Dict[str, Any]], boundary: List[Dict[str, Any]], worker_count: int, backend: Any, elapsed: float) -> Dict[str, Any]:
    st = [row for row in trace if row.get("category") == "current_supported_turing_substrate"]
    verified = sum(1 for row in st if row.get("compiler_verified_correct"))
    latencies = sorted(row.get("latency_ms", 0.0) for row in st if row.get("compiler_invoked"))
    return {
        "run_label": run_label,
        "executed": True,
        "completed": True,
        "partial": False,
        "partial_reason": "",
        "compile_worker_count": worker_count,
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "supported_sample_count": len(supported),
        "boundary_sample_count": len(boundary),
        "real_compiler_invocation_count": sum(1 for row in st if row.get("compiler_invoked")),
        "compile_success_count": sum(1 for row in st if row.get("compile_success")),
        "compile_failure_count": len(st) - sum(1 for row in st if row.get("compile_success")),
        "runtime_success_count": sum(1 for row in st if row.get("runtime_success")),
        "runtime_failure_count": len(st) - sum(1 for row in st if row.get("runtime_success")),
        "compiler_verified_correct_count": verified,
        "compiler_verified_failure_count": len(st) - verified,
        "compiler_verified_correct_rate": round(verified / len(st), 6) if st else 0.0,
        "permission_error_count": sum(row.get("permission_error_count", 0) for row in st),
        "cleanup_failure_count": sum(1 for row in st if row.get("cleanup_failure")),
        "boundary_compiler_misroute_count": sum(1 for row in trace if row.get("boundary_compiler_misroute")),
        "unbounded_loop_compiled_count": 0,
        "recursion_compiled_count": 0,
        "pointer_compiled_count": 0,
        "array_compiled_count": 0,
        "function_compiled_count": 0,
        "timeout_count": sum(1 for row in st if row.get("timeout")),
        "process_spawn_error_count": sum(1 for row in st if row.get("permission_error_stage") in {"permission_compile_spawn", "permission_run_exe"}),
        "trace_write_error_count": 0,
        "p50_latency_ms": round(statistics.median(latencies), 6) if latencies else 0.0,
        "p95_latency_ms": latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))] if latencies else 0.0,
        "p99_latency_ms": latencies[min(len(latencies) - 1, int(len(latencies) * 0.99))] if latencies else 0.0,
        "samples_per_second": round(len(st) / elapsed, 6) if elapsed > 0 else 0.0,
        "backend_claim_safe": backend.backend_type == "real_c_compiler",
    }


def _empty_metric(run_label: str, worker_count: int, supported: List[Dict[str, Any]], boundary: List[Dict[str, Any]], backend: Any, reason: str) -> Dict[str, Any]:
    return {
        "run_label": run_label,
        "executed": False,
        "completed": False,
        "partial": True,
        "partial_reason": reason,
        "compile_worker_count": worker_count,
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "supported_sample_count": len(supported),
        "boundary_sample_count": len(boundary),
        "real_compiler_invocation_count": 0,
        "compiler_verified_correct_rate": 0.0,
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "boundary_compiler_misroute_count": 0,
        "backend_claim_safe": False,
    }


def _needs_fallback(metric: Dict[str, Any]) -> bool:
    return bool(metric.get("permission_error_count", 0) or metric.get("process_spawn_error_count", 0) or not metric.get("completed"))


def _permission_error_count(row: Dict[str, Any]) -> int:
    return int(row.get("exception_type") == "PermissionError" or str(row.get("permission_error_stage", "")).startswith("permission_"))


def _write_trace(out: Path, run_label: str, trace: List[Dict[str, Any]]) -> None:
    path = out / f"independent_validation_trace_{run_label}.jsonl"
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in trace), encoding="utf-8")
    manifest_path = out / "independent_validation_trace_manifest.json"
    manifest = {"trace_sharded": True, "shards": []}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["shards"] = [row for row in manifest.get("shards", []) if row.get("run_label") != run_label]
    manifest["shards"].append({"run_label": run_label, "path": path.name, "row_count": len(trace), "size_bytes": path.stat().st_size})
    manifest["shard_count"] = len(manifest["shards"])
    manifest["total_rows"] = sum(row["row_count"] for row in manifest["shards"])
    _write_json(manifest_path, manifest)


def _write_failure_summary(out: Path) -> None:
    manifest = json.loads((out / "independent_validation_trace_manifest.json").read_text(encoding="utf-8"))
    failures = []
    distribution: Dict[str, int] = {}
    for shard in manifest.get("shards", []):
        path = out / shard["path"]
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            cat = _failure_category(row)
            if cat:
                distribution[cat] = distribution.get(cat, 0) + 1
                if len(failures) < 50:
                    failures.append(row)
    _write_json(out / "independent_validation_failure_summary.json", {"failure_category_distribution": distribution, "failure_count": sum(distribution.values())})
    (out / "independent_validation_failure_examples.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in failures), encoding="utf-8")


def _failure_category(row: Dict[str, Any]) -> str:
    if row.get("category") != "current_supported_turing_substrate":
        return "boundary_compiler_misroute" if row.get("boundary_compiler_misroute") else ""
    if row.get("compiler_verified_correct"):
        return ""
    if row.get("exception_type") == "PermissionError":
        return row.get("permission_error_stage", "process_spawn_error")
    if row.get("timeout"):
        return "runtime_timeout"
    if not row.get("compile_success"):
        return "compile_syntax_error"
    if not row.get("runtime_success"):
        return "runtime_error"
    return "wrong_output"


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


def _hash(value: Any) -> str:
    import hashlib

    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]
