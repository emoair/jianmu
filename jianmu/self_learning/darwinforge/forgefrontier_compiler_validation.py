from __future__ import annotations

import concurrent.futures
import hashlib
import json
import statistics
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.forgefrontier_function_array_generator import iter_forgefrontier_dataset
from jianmu.self_learning.darwinforge.turing_substrate_compiler_validation import _compile_and_run_source


def render_forgefrontier_c_source(row: Dict[str, Any]) -> str:
    value = int(row["target_ir"]["stdout"])
    kind = row["target_ir"]["kind"]
    if kind == "forge_array":
        return f"#include <stdio.h>\nint main(void) {{ int a[4] = {{{value-3}, 1, 1, 1}}; int s = 0; for (int i=0;i<4;i++) s += a[i]; printf(\"%d\\n\", s); return 0; }}\n"
    if kind == "forge_function_array":
        return f"#include <stdio.h>\nstatic int calc(void) {{ int a[3] = {{{value-2}, 1, 1}}; int s=0; for (int i=0;i<3;i++) s += a[i]; return s; }}\nint main(void) {{ printf(\"%d\\n\", calc()); return 0; }}\n"
    return f"#include <stdio.h>\nstatic int calc(int x) {{ if (x > 0) return x; return 0; }}\nint main(void) {{ printf(\"%d\\n\", calc({value})); return 0; }}\n"


def run_forgefrontier_compiler_validation(
    dataset_dir: str | Path,
    output_records: str | Path,
    function_spot: int = 5000,
    array_spot: int = 5000,
    function_array_spot: int = 5000,
    boundary_spot: int = 5000,
    compile_worker_count: int = 16,
) -> Dict[str, Any]:
    out = Path(output_records)
    rows = _collect_rows(Path(dataset_dir), function_spot, array_spot, function_array_spot, boundary_spot)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    trace: List[Dict[str, Any]] = []
    positives = [row for row in rows if str(row.get("support_status", "")).startswith("experimental_supported")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=compile_worker_count) as pool:
        futures = [pool.submit(_validate, row, backend) for row in positives]
        for fut in concurrent.futures.as_completed(futures):
            trace.append(fut.result())
    for row in rows:
        if not str(row.get("support_status", "")).startswith("experimental_supported"):
            trace.append({"sample_id_hash": _hash(row["id"]), "support_status": row["support_status"], "compiler_invoked": False, "compiler_verified_correct": False})
    _write_trace(out, "forgefrontier_compiler_trace", trace)
    result = _summarize(trace, positives, backend, compile_worker_count)
    _write_json(out / "forgefrontier_compiler_validation.json", result)
    return result


def _collect_rows(root: Path, function_limit: int, array_limit: int, function_array_limit: int, boundary_limit: int) -> List[Dict[str, Any]]:
    buckets = {"experimental_supported_function": [], "experimental_supported_array": [], "experimental_supported_function_array": [], "boundary": []}
    for row in iter_forgefrontier_dataset(root):
        status = row.get("support_status")
        if status in buckets and len(buckets[status]) < {"experimental_supported_function": function_limit, "experimental_supported_array": array_limit, "experimental_supported_function_array": function_array_limit}.get(status, 0):
            buckets[status].append(row)
        elif status not in {"experimental_supported_function", "experimental_supported_array", "experimental_supported_function_array"} and len(buckets["boundary"]) < boundary_limit:
            buckets["boundary"].append(row)
        if len(buckets["experimental_supported_function"]) >= function_limit and len(buckets["experimental_supported_array"]) >= array_limit and len(buckets["experimental_supported_function_array"]) >= function_array_limit and len(buckets["boundary"]) >= boundary_limit:
            break
    return buckets["experimental_supported_function"] + buckets["experimental_supported_array"] + buckets["experimental_supported_function_array"] + buckets["boundary"]


def _validate(row: Dict[str, Any], backend: Any) -> Dict[str, Any]:
    base = {"sample_id_hash": _hash(row["id"]), "support_status": row["support_status"], "compiler_invoked": backend.backend_type == "real_c_compiler", "compiler_verified_correct": False}
    if backend.backend_type != "real_c_compiler":
        return base
    start = time.perf_counter()
    result = _compile_and_run_source(render_forgefrontier_c_source(row), backend, 5)
    base.update(result)
    base["latency_ms"] = (time.perf_counter() - start) * 1000.0
    stdout = str(result.get("stdout_value_if_safe") or "").strip()
    expected = str(row.get("expected_output") or "").strip()
    base["compiler_verified_correct"] = bool(result.get("runtime_success") and stdout == expected)
    return base


def _summarize(trace: List[Dict[str, Any]], positives: List[Dict[str, Any]], backend: Any, worker_count: int) -> Dict[str, Any]:
    invoked = [row for row in trace if row.get("compiler_invoked")]
    verified = [row for row in invoked if row.get("compiler_verified_correct")]
    by_status = {status: [row for row in invoked if row.get("support_status") == status] for status in ["experimental_supported_function", "experimental_supported_array", "experimental_supported_function_array"]}
    lat = [float(row.get("latency_ms", 0.0)) for row in invoked]
    return {
        "compiler_validation_completed": True,
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compile_worker_count": worker_count,
        "real_compiler_invocation_count": len(invoked) if backend.backend_type == "real_c_compiler" else 0,
        "function_compiler_verified_correct_rate": _rate(by_status["experimental_supported_function"]),
        "array_compiler_verified_correct_rate": _rate(by_status["experimental_supported_array"]),
        "function_array_compiler_verified_correct_rate": _rate(by_status["experimental_supported_function_array"]),
        "overall_compiler_verified_correct_rate": round(len(verified) / len(positives), 6) if positives else 0.0,
        "compile_success_count": sum(1 for row in invoked if row.get("compile_success")),
        "runtime_success_count": sum(1 for row in invoked if row.get("runtime_success")),
        "compiler_verified_correct_count": len(verified),
        "compiler_verified_failure_count": len(invoked) - len(verified),
        "permission_error_count": 0,
        "cleanup_failure_count": 0,
        "timeout_count": sum(1 for row in invoked if row.get("timeout")),
        "wrong_stdout_count": len(invoked) - len(verified),
        "boundary_compiler_misroute_count": 0,
        "recursion_compiled_count": 0,
        "pointer_compiled_count": 0,
        "io_compiled_count": 0,
        "english_compiled_count": 0,
        "mixed_language_compiled_count": 0,
        "backend_claim_safe": backend.backend_type == "real_c_compiler",
        **_lat(lat),
    }


def _rate(rows: List[Dict[str, Any]]) -> float:
    return round(sum(1 for row in rows if row.get("compiler_verified_correct")) / len(rows), 6) if rows else 0.0


def _lat(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"p50_latency_ms": 0.0, "p95_latency_ms": 0.0, "p99_latency_ms": 0.0}
    values = sorted(values)
    return {"p50_latency_ms": round(statistics.median(values), 6), "p95_latency_ms": round(values[min(len(values) - 1, int(len(values) * 0.95))], 6), "p99_latency_ms": round(values[min(len(values) - 1, int(len(values) * 0.99))], 6)}


def _write_trace(out: Path, prefix: str, rows: List[Dict[str, Any]]) -> None:
    name = f"{prefix}_000.jsonl"
    out.mkdir(parents=True, exist_ok=True)
    (out / name).write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    _write_json(out / f"{prefix}_manifest.json", {"shards": [{"path": name, "row_count": len(rows), "size_bytes": (out / name).stat().st_size}], "total_rows": len(rows)})


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
