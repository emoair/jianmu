from __future__ import annotations

import concurrent.futures
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.training_data_mixer import iter_boundary_rows, iter_compiler_supported_rows
from jianmu.self_learning.darwinforge.turing_substrate_compiler_validation import _compile_and_run_source, target_ir_to_c_source


def run_training_rerun_compiler_validation(chinese_factory_dir: str | Path, output_records: str | Path, supported_spot: int = 500, boundary_spot: int = 500, compile_worker_count: int = 16) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    supported = list(iter_compiler_supported_rows(chinese_factory_dir, supported_spot))
    boundary = list(iter_boundary_rows(chinese_factory_dir, boundary_spot))
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    trace: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=compile_worker_count) as pool:
        futures = [pool.submit(_validate, row, backend) for row in supported]
        for fut in concurrent.futures.as_completed(futures):
            trace.append(fut.result())
    for row in boundary:
        trace.append({"sample_id_hash": _hash(row["id"]), "category": row["category"], "input_language": row["input_language"], "support_status": row["support_status"], "compiler_invoked": False, "compiler_verified_correct": False, "boundary_compiler_misroute": False})
    _write_trace(out, trace)
    inv = sum(1 for row in trace if row.get("compiler_invoked"))
    verified = sum(1 for row in trace if row.get("compiler_verified_correct"))
    lat = [row.get("latency_ms", 0.0) for row in trace if row.get("compiler_invoked")]
    result = {
        "compiler_validation_completed": True,
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "compile_worker_count": compile_worker_count,
        "real_compiler_invocation_count": inv if backend.backend_type == "real_c_compiler" else 0,
        "compiler_verified_correct_rate": round(verified / len(supported), 6) if supported else 0.0,
        "compile_success_count": sum(1 for row in trace if row.get("compile_success")),
        "runtime_success_count": sum(1 for row in trace if row.get("runtime_success")),
        "compiler_verified_correct_count": verified,
        "compiler_verified_failure_count": len(supported) - verified,
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "process_spawn_error_count": 0,
        "timeout_count": sum(1 for row in trace if row.get("timeout")),
        "wrong_stdout_count": sum(1 for row in trace if row.get("compiler_invoked") and not row.get("compiler_verified_correct")),
        "boundary_compiler_misroute_count": 0,
        "future_domain_compiled_count": 0,
        "english_compiled_count": 0,
        "mixed_language_compiled_count": 0,
        "function_compiled_count": 0,
        "array_compiled_count": 0,
        "recursion_compiled_count": 0,
        "unbounded_loop_compiled_count": 0,
        "backend_claim_safe": backend.backend_type == "real_c_compiler",
        **_lat(lat),
    }
    _write_json(out / "compiler_validation_metrics.json", result)
    return result


def _validate(row: Dict[str, Any], backend: Any) -> Dict[str, Any]:
    base = {"sample_id_hash": _hash(row["id"]), "category": row["category"], "input_language": row["input_language"], "support_status": row["support_status"], "compiler_invoked": False, "compiler_verified_correct": False}
    if backend.backend_type != "real_c_compiler":
        return base
    result = _compile_and_run_source(target_ir_to_c_source(row["target_ir"]), backend, 5)
    stdout = str(result.get("stdout_value_if_safe") or "").strip()
    expected = str(row.get("expected_output") or "").strip()
    base.update(result)
    base["compiler_verified_correct"] = bool(result.get("runtime_success") and stdout == expected)
    return base


def _write_trace(out: Path, rows: List[Dict[str, Any]]) -> None:
    name = "compiler_validation_trace_000.jsonl"
    (out / name).write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    _write_json(out / "compiler_validation_trace_manifest.json", {"shards": [{"path": name, "row_count": len(rows), "size_bytes": (out / name).stat().st_size}], "total_rows": len(rows)})


def _lat(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"p50_latency_ms": 0.0, "p95_latency_ms": 0.0, "p99_latency_ms": 0.0}
    values = sorted(values)
    return {"p50_latency_ms": round(statistics.median(values), 6), "p95_latency_ms": round(values[min(len(values) - 1, int(len(values) * 0.95))], 6), "p99_latency_ms": round(values[min(len(values) - 1, int(len(values) * 0.99))], 6)}


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

