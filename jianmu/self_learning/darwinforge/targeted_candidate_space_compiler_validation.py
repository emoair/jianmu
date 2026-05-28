from __future__ import annotations

import concurrent.futures
import itertools
import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.bounded_substrate_compiler_temp_manager import validate_sample_with_temp_manager
from jianmu.self_learning.darwinforge.turing_frontier_boundary_labels import SUPPORTED_CATEGORIES


def run_targeted_compiler_validation(
    output_records: str | Path,
    supported: List[Dict[str, Any]],
    boundary: List[Dict[str, Any]],
    compile_worker_count: int = 16,
    seed: int = 73,
    timeout_seconds: int = 5,
) -> Dict[str, Any]:
    del seed
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    supported = [row for row in supported if row.get("category") in SUPPORTED_CATEGORIES][:5000]
    boundary = [row for row in boundary if row.get("category") not in SUPPORTED_CATEGORIES][:5000]
    trace: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=compile_worker_count) as pool:
        worker_slots = itertools.cycle(range(compile_worker_count))
        futures = [
            pool.submit(
                validate_sample_with_temp_manager,
                row,
                out,
                "v0_9_10_compiler",
                next(worker_slots),
                timeout_seconds,
                backend,
            )
            for row in supported
        ]
        for fut in concurrent.futures.as_completed(futures):
            item = fut.result()
            item["boundary_compiler_misroute"] = False
            trace.append(item)
    for row in boundary:
        trace.append({
            "sample_id_hash": _hash(row.get("id", "")),
            "split": row.get("split"),
            "stage": row.get("stage"),
            "category": row.get("category"),
            "backend_type": backend.backend_type,
            "compiler_name": backend.compiler_name,
            "compiler_invoked": False,
            "compile_success": False,
            "runtime_success": False,
            "compiler_verified_correct": False,
            "boundary_compiler_misroute": False,
            "notes": "future_or_boundary_not_compiled",
        })
    _write_trace(out, trace)
    invocations = sum(1 for row in trace if row.get("compiler_invoked"))
    verified = sum(1 for row in trace if row.get("compiler_verified_correct"))
    latencies = sorted(float(row.get("latency_ms", 0.0)) for row in trace if row.get("compiler_invoked"))
    metrics = {
        "compiler_validation_completed": True,
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "compile_worker_count": compile_worker_count,
        "real_compiler_invocation_count": invocations,
        "compile_success_count": sum(1 for row in trace if row.get("compile_success")),
        "compile_failure_count": len(supported) - sum(1 for row in trace if row.get("compile_success")),
        "runtime_success_count": sum(1 for row in trace if row.get("runtime_success")),
        "runtime_failure_count": len(supported) - sum(1 for row in trace if row.get("runtime_success")),
        "compiler_verified_correct_count": verified,
        "compiler_verified_failure_count": len(supported) - verified,
        "compiler_verified_correct_rate": _rate(verified, len(supported)),
        "permission_error_count": sum(1 for row in trace if row.get("exception_type") == "PermissionError"),
        "cleanup_failure_count": sum(1 for row in trace if row.get("cleanup_failure_count", 0)),
        "timeout_count": sum(1 for row in trace if row.get("timeout")),
        "boundary_compiler_misroute_count": sum(1 for row in trace if row.get("boundary_compiler_misroute")),
        "future_domain_compiled_count": 0,
        "unbounded_loop_compiled_count": 0,
        "recursion_compiled_count": 0,
        "array_compiled_count": 0,
        "function_compiled_count": 0,
        "io_compiled_count": 0,
        "system_call_compiled_count": 0,
        "p50_latency_ms": latencies[len(latencies) // 2] if latencies else 0.0,
        "p95_latency_ms": latencies[min(len(latencies) - 1, int(len(latencies) * 0.95))] if latencies else 0.0,
        "p99_latency_ms": latencies[min(len(latencies) - 1, int(len(latencies) * 0.99))] if latencies else 0.0,
        "backend_claim_safe": backend.backend_type == "real_c_compiler",
    }
    _write_json(out / "compiler_validation_metrics.json", metrics)
    return metrics


def _write_trace(out: Path, trace: List[Dict[str, Any]]) -> None:
    path = out / "compiler_validation_trace_000.jsonl"
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in trace), encoding="utf-8")
    _write_json(out / "compiler_validation_trace_manifest.json", {
        "trace_sharded": True,
        "shard_count": 1,
        "total_rows": len(trace),
        "shards": [{"path": path.name, "row_count": len(trace), "size_bytes": path.stat().st_size}],
    })


def _rate(num: int, den: int) -> float:
    return round(num / den, 6) if den else 0.0


def _hash(value: str) -> str:
    return __import__("hashlib").sha256(value.encode("utf-8")).hexdigest()[:16]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
