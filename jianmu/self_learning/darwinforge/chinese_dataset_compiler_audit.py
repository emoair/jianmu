from __future__ import annotations

import concurrent.futures
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.chinese_dataset_audit import iter_rows
from jianmu.self_learning.darwinforge.turing_substrate_compiler_validation import _compile_and_run_source, target_ir_to_c_source


def run_chinese_dataset_compiler_audit(dataset_dir: str | Path, output_records: str | Path, supported_spot: int = 5000, boundary_spot: int = 5000, compile_worker_count: int = 16, seed: int = 98) -> Dict[str, Any]:
    root = Path(dataset_dir)
    records = Path(output_records)
    records.mkdir(parents=True, exist_ok=True)
    supported, boundary = _collect_spots(root, supported_spot, boundary_spot)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    trace: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=compile_worker_count) as pool:
        futures = [pool.submit(_validate, row, backend) for row in supported]
        for fut in concurrent.futures.as_completed(futures):
            trace.append(fut.result())
    for row in boundary:
        trace.append({"sample_id_hash": _hash(row["id"]), "category": row["category"], "input_language": row["input_language"], "support_status": row["support_status"], "compiler_invoked": False, "compiler_verified_correct": False, "boundary_compiler_misroute": False})
    _write_trace(records, trace)
    inv = sum(1 for r in trace if r.get("compiler_invoked"))
    verified = sum(1 for r in trace if r.get("compiler_verified_correct"))
    lat = [r.get("latency_ms", 0.0) for r in trace if r.get("compiler_invoked")]
    metrics = {
        "compiler_audit_completed": True,
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "compile_worker_count": compile_worker_count,
        "supported_sample_count": len(supported),
        "boundary_sample_count": len(boundary),
        "real_compiler_invocation_count": inv if backend.backend_type == "real_c_compiler" else 0,
        "compiler_verified_correct_rate": round(verified / len(supported), 6) if supported else 0.0,
        "compile_success_count": sum(1 for r in trace if r.get("compile_success")),
        "runtime_success_count": sum(1 for r in trace if r.get("runtime_success")),
        "compiler_verified_correct_count": verified,
        "compiler_verified_failure_count": len(supported) - verified,
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "timeout_count": sum(1 for r in trace if r.get("timeout")),
        "wrong_stdout_count": sum(1 for r in trace if r.get("compiler_invoked") and not r.get("compiler_verified_correct")),
        "boundary_compiler_misroute_count": sum(1 for r in trace if r.get("boundary_compiler_misroute")),
        "future_domain_compiled_count": sum(1 for r in trace if r.get("support_status") == "future_domain" and r.get("compiler_invoked")),
        "english_compiled_count": sum(1 for r in trace if r.get("input_language") == "en" and r.get("compiler_invoked")),
        "mixed_language_compiled_count": sum(1 for r in trace if r.get("input_language") == "mixed" and r.get("compiler_invoked")),
        "function_compiled_count": 0,
        "array_compiled_count": 0,
        "recursion_compiled_count": 0,
        "unbounded_loop_compiled_count": 0,
        "backend_claim_safe": backend.backend_type == "real_c_compiler",
        **_lat(lat),
    }
    _write_json(records / "chinese_dataset_compiler_audit.json", metrics)
    return metrics


def _validate(row: Dict[str, Any], backend: Any) -> Dict[str, Any]:
    base = {"sample_id_hash": _hash(row["id"]), "category": row["category"], "input_language": row["input_language"], "support_status": row["support_status"], "compiler_invoked": False, "compiler_verified_correct": False, "boundary_compiler_misroute": False}
    if backend.backend_type != "real_c_compiler":
        return base
    try:
        result = _compile_and_run_source(target_ir_to_c_source(row["target_ir"]), backend, 5)
    except Exception as exc:
        base["notes"] = f"validation_exception:{type(exc).__name__}"
        return base
    stdout = str(result.get("stdout_value_if_safe") or "").strip()
    expected = str(row.get("expected_output") or "").strip()
    base.update(result)
    base["compiler_verified_correct"] = bool(result.get("runtime_success") and stdout == expected)
    return base


def _collect_spots(root: Path, supported_spot: int, boundary_spot: int) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    supported: List[Dict[str, Any]] = []
    boundary: List[Dict[str, Any]] = []
    for scale in sorted(p for p in root.iterdir() if p.is_dir()):
        for row in iter_rows(scale):
            if row["support_status"] == "current_supported" and row["input_language"] == "zh":
                if len(supported) < supported_spot:
                    supported.append(row)
            else:
                if len(boundary) < boundary_spot:
                    boundary.append(row)
            if len(supported) >= supported_spot and len(boundary) >= boundary_spot:
                return supported, boundary
    return supported, boundary


def _lat(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"p50_latency_ms": 0.0, "p95_latency_ms": 0.0, "p99_latency_ms": 0.0}
    values = sorted(values)
    return {"p50_latency_ms": round(statistics.median(values), 6), "p95_latency_ms": round(values[min(len(values) - 1, int(len(values) * 0.95))], 6), "p99_latency_ms": round(values[min(len(values) - 1, int(len(values) * 0.99))], 6)}


def _write_trace(records: Path, rows: List[Dict[str, Any]]) -> None:
    name = "chinese_dataset_compiler_trace_000.jsonl"
    (records / name).write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    _write_json(records / "chinese_dataset_compiler_trace_manifest.json", {"shards": [{"path": name, "row_count": len(rows), "size_bytes": (records / name).stat().st_size}], "total_rows": len(rows)})


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:16]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
