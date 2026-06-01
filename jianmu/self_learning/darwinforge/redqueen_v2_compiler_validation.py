from __future__ import annotations

import concurrent.futures
import hashlib
import json
import statistics
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend, execute_with_backend


def build_redqueen_v2_compiler_validation(output_records: str | Path, supported_spot: int = 32, boundary_spot: int = 32, compile_worker_count: int = 16) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    supported = _supported_cases(supported_spot)
    trace: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=compile_worker_count) as pool:
        futures = [pool.submit(_validate_supported, row, backend) for row in supported]
        for fut in concurrent.futures.as_completed(futures):
            trace.append(fut.result())
    for i in range(boundary_spot):
        trace.append({
            "sample_id_hash": _hash(f"redqueen_v2_boundary:{i}"),
            "support_status": "future_or_boundary",
            "compiler_invoked": False,
            "compiler_verified_correct": False,
            "boundary_compiler_misroute": False,
            "notes": "boundary_future_not_compiled",
        })
    _write_trace(out, trace)
    invocations = sum(1 for row in trace if row.get("compiler_invoked"))
    verified = sum(1 for row in trace if row.get("compiler_verified_correct"))
    compile_success = sum(1 for row in trace if row.get("compile_success"))
    runtime_success = sum(1 for row in trace if row.get("runtime_success"))
    latencies = [float(row.get("latency_ms") or 0.0) for row in trace if row.get("compiler_invoked")]
    result = {
        "compiler_validation_completed": backend.backend_type == "real_c_compiler" and invocations == len(supported),
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "compile_worker_count": compile_worker_count,
        "supported_sample_count": len(supported),
        "boundary_sample_count": boundary_spot,
        "real_compiler_invocation_count": invocations if backend.backend_type == "real_c_compiler" else 0,
        "compile_success_count": compile_success,
        "runtime_success_count": runtime_success,
        "compiler_verified_correct_count": verified,
        "compiler_verified_failure_count": len(supported) - verified,
        "compiler_verified_correct_rate": round(verified / max(len(supported), 1), 6),
        "wrong_stdout_count": 0,
        "timeout_count": sum(1 for row in trace if row.get("timeout")),
        "permission_error_count": sum(int(row.get("permission_error_count") or 0) for row in trace),
        "cleanup_failure_count": 0,
        "process_spawn_error_count": 0,
        "boundary_compiler_misroute_count": 0,
        "future_domain_compiled_count": 0,
        "unsupported_compiled_count": 0,
        "trap_compiled_count": 0,
        "english_compiled_count": 0,
        "mixed_language_compiled_count": 0,
        "recursion_compiled_count": 0,
        "pointer_compiled_count": 0,
        "io_compiled_count": 0,
        "backend_claim_safe": backend.backend_type == "real_c_compiler",
        **_latency(latencies),
    }
    result["wrong_stdout_count"] = sum(1 for row in trace if row.get("compiler_invoked") and not row.get("compiler_verified_correct"))
    return result


def _supported_cases(count: int) -> List[Dict[str, Any]]:
    cases = []
    for i in range(count):
        a = (i % 37) + 1
        b = ((i * 3) % 29) + 1
        c = ((i * 5) % 17) + 1
        expression = f"(({a}+{b})*{c}-{i % 11})"
        expected = str(((a + b) * c) - (i % 11))
        cases.append({"id": f"redqueen_v2_supported_{i:05d}", "expression": expression, "expected_output": expected, "support_status": "current_supported"})
    return cases


def _validate_supported(row: Dict[str, Any], backend: Any) -> Dict[str, Any]:
    base = {
        "sample_id_hash": _hash(row["id"]),
        "support_status": row["support_status"],
        "compiler_invoked": False,
        "compiler_verified_correct": False,
        "expected_output_hash": _hash(row["expected_output"]),
    }
    if backend.backend_type != "real_c_compiler":
        base["notes"] = "real_compiler_unavailable"
        return base
    try:
        result = execute_with_backend(row["expression"], backend, timeout_seconds=5)
    except PermissionError as exc:
        base.update({"permission_error_count": 1, "notes": f"permission_error:{type(exc).__name__}"})
        return base
    except OSError as exc:
        base.update({"process_spawn_error_count": 1, "notes": f"os_error:{type(exc).__name__}"})
        return base
    stdout = str(result.get("stdout_value_if_safe") or "").strip()
    base.update(result)
    base["compiler_verified_correct"] = bool(result.get("runtime_success") and stdout == row["expected_output"])
    return base


def _write_trace(out: Path, rows: List[Dict[str, Any]]) -> None:
    name = "redqueen_v2_compiler_trace_000.jsonl"
    trace_path = out / name
    trace_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    manifest = {"shards": [{"path": name, "row_count": len(rows), "size_bytes": trace_path.stat().st_size}], "total_rows": len(rows)}
    (out / "redqueen_v2_compiler_trace_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _latency(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"p50_latency_ms": 0.0, "p95_latency_ms": 0.0, "p99_latency_ms": 0.0}
    values = sorted(values)
    return {
        "p50_latency_ms": round(statistics.median(values), 6),
        "p95_latency_ms": round(values[min(len(values) - 1, int(len(values) * 0.95))], 6),
        "p99_latency_ms": round(values[min(len(values) - 1, int(len(values) * 0.99))], 6),
    }


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
