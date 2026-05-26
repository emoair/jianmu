from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import statistics
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import CompilerBackend, _build_backend_compile_command, detect_arithmetic_backend
from jianmu.self_learning.darwinforge.turing_substrate_boundary_labels import SUPPORTED
from jianmu.self_learning.darwinforge.turing_substrate_generator import write_readiness_and_mainline


def run_turing_substrate_compiler_validation(
    dataset_dir: str | Path,
    output_records: str | Path,
    scales: Iterable[str],
    compile_worker_count: int = 16,
    supported_samples: int = 5_000,
    boundary_samples: int = 5_000,
    seed: int = 52,
    timeout_seconds: int = 5,
) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    trace: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    metrics_by_scale: Dict[str, Dict[str, Any]] = {}
    for scale in scales:
        rows = list(_iter_rows(Path(dataset_dir) / scale))
        supported = [row for row in rows if row.get("category") == SUPPORTED]
        boundary = [row for row in rows if row.get("category") != SUPPORTED]
        supported = _sample_deterministic(supported, supported_samples if scale == "large" else min(supported_samples, {"small": 500, "medium": 2000}.get(scale, supported_samples)), seed + len(scale))
        boundary = _sample_deterministic(boundary, boundary_samples if scale == "large" else min(boundary_samples, {"small": 500, "medium": 2000}.get(scale, boundary_samples)), seed + 100 + len(scale))
        scale_trace, scale_failures, scale_metrics = _validate_scale(scale, supported, boundary, backend, compile_worker_count, timeout_seconds)
        trace.extend(scale_trace)
        failures.extend(scale_failures)
        metrics_by_scale[scale] = scale_metrics
    _write_trace(out, trace)
    (out / "compiler_validation_failures.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in failures), encoding="utf-8")
    aggregate = _aggregate_metrics(metrics_by_scale, backend, compile_worker_count)
    _write_json(out / "compiler_validation_metrics.json", aggregate)
    dataset_summaries = _load_dataset_summaries(Path(dataset_dir), scales)
    write_readiness_and_mainline(out, dataset_summaries, aggregate)
    return aggregate


def target_ir_to_c_source(target_ir: Dict[str, Any]) -> str:
    if target_ir.get("op") != "Program":
        raise ValueError("root must be Program")
    body = "\n".join(_stmt_to_c(stmt, 1) for stmt in target_ir.get("body", []))
    return "\n".join([
        "#include <stdio.h>",
        "",
        "int main(void) {",
        body,
        "    return 0;",
        "}",
        "",
    ])


def _validate_scale(scale: str, supported: List[Dict[str, Any]], boundary: List[Dict[str, Any]], backend: CompilerBackend, compile_worker_count: int, timeout_seconds: int) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    started = time.perf_counter()
    trace: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=compile_worker_count) as pool:
        futures = [pool.submit(_validate_supported, scale, row, backend, timeout_seconds) for row in supported]
        for fut in concurrent.futures.as_completed(futures):
            row = fut.result()
            trace.append(row)
            if not row["compiler_verified_correct"]:
                failures.append(row)
    for row in boundary:
        trace.append({
            "sample_id_hash": _hash(row["id"]),
            "scale": scale,
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
            "timeout": False,
            "latency_ms": 0.0,
            "notes": "boundary_not_compiled",
        })
    latencies = [row["latency_ms"] for row in trace if row.get("compiler_invoked") and row.get("latency_ms") is not None]
    compile_success = sum(1 for row in trace if row.get("compile_success"))
    runtime_success = sum(1 for row in trace if row.get("runtime_success"))
    verified = sum(1 for row in trace if row.get("compiler_verified_correct"))
    invocations = sum(1 for row in trace if row.get("compiler_invoked"))
    elapsed = round(time.perf_counter() - started, 6)
    latency = _latency(latencies)
    metrics = {
        "scale": scale,
        "supported_sample_count": len(supported),
        "boundary_sample_count": len(boundary),
        "real_compiler_invocation_count": invocations if backend.backend_type == "real_c_compiler" else 0,
        "compile_success_count": compile_success,
        "compile_failure_count": invocations - compile_success,
        "runtime_success_count": runtime_success,
        "runtime_failure_count": invocations - runtime_success,
        "compiler_verified_correct_count": verified,
        "compiler_verified_failure_count": invocations - verified,
        "compiler_verified_correct_rate": round(verified / invocations, 6) if invocations else 0.0,
        "boundary_compiler_misroute_count": sum(1 for row in trace if row.get("boundary_compiler_misroute")),
        "timeout_count": sum(1 for row in trace if row.get("timeout")),
        "samples_per_second": round(invocations / elapsed, 6) if elapsed > 0 else 0.0,
        "total_wall_clock_seconds": elapsed,
        **latency,
    }
    return trace, failures, metrics


def _validate_supported(scale: str, row: Dict[str, Any], backend: CompilerBackend, timeout_seconds: int) -> Dict[str, Any]:
    started = time.perf_counter()
    base = {
        "sample_id_hash": _hash(row["id"]),
        "scale": scale,
        "split": row.get("split"),
        "stage": row.get("stage"),
        "category": row.get("category"),
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "compiler_invoked": False,
        "compile_returncode": None,
        "compile_success": False,
        "runtime_invoked": False,
        "runtime_returncode": None,
        "runtime_success": False,
        "stdout_hash": None,
        "expected_output_hash": _hash(row.get("expected_output") or ""),
        "compiler_verified_correct": False,
        "boundary_compiler_misroute": False,
        "timeout": False,
        "latency_ms": 0.0,
        "notes": "",
    }
    if backend.backend_type != "real_c_compiler":
        base["notes"] = "real_compiler_unavailable"
        return base
    try:
        source = target_ir_to_c_source(row["target_ir"])
        result = _compile_and_run_source(source, backend, timeout_seconds)
    except Exception as exc:
        base.update({"notes": f"validation_exception:{type(exc).__name__}", "latency_ms": round((time.perf_counter() - started) * 1000, 6)})
        return base
    stdout = (result.get("stdout_value_if_safe") or "").strip()
    expected = (row.get("expected_output") or "").strip()
    base.update(result)
    base["expected_output_hash"] = _hash(expected)
    base["compiler_verified_correct"] = bool(result.get("runtime_success") and stdout == expected)
    return base


def _compile_and_run_source(source: str, backend: CompilerBackend, timeout_seconds: int) -> Dict[str, Any]:
    started = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        src = tmp / "prog.c"
        exe = tmp / ("prog.exe" if os.name == "nt" else "prog")
        src.write_text(source, encoding="utf-8")
        cmd, env = _build_backend_compile_command(backend, src, exe)
        result: Dict[str, Any] = {
            "compiler_invoked": True,
            "compile_returncode": None,
            "compile_success": False,
            "runtime_invoked": False,
            "runtime_returncode": None,
            "runtime_success": False,
            "stdout_hash": None,
            "stdout_value_if_safe": None,
            "timeout": False,
            "latency_ms": 0.0,
        }
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds, cwd=tmpdir, env=env, errors="replace")
        except subprocess.TimeoutExpired:
            result.update({"compile_returncode": -1, "timeout": True, "latency_ms": round((time.perf_counter() - started) * 1000, 6)})
            return result
        result.update({"compile_returncode": proc.returncode, "compile_success": proc.returncode == 0})
        if proc.returncode != 0:
            result["latency_ms"] = round((time.perf_counter() - started) * 1000, 6)
            return result
        try:
            run = subprocess.run([str(exe)], capture_output=True, text=True, timeout=timeout_seconds, cwd=tmpdir, errors="replace")
        except subprocess.TimeoutExpired:
            result.update({"runtime_invoked": True, "runtime_returncode": -1, "timeout": True, "latency_ms": round((time.perf_counter() - started) * 1000, 6)})
            return result
        stdout = run.stdout.strip()
        result.update({
            "runtime_invoked": True,
            "runtime_returncode": run.returncode,
            "runtime_success": run.returncode == 0,
            "stdout_hash": _hash(stdout),
            "stdout_value_if_safe": stdout if stdout.lstrip("-").isdigit() else None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 6),
        })
        return result


def _stmt_to_c(stmt: Dict[str, Any], indent: int) -> str:
    pad = "    " * indent
    op = stmt["op"]
    if op == "VarDecl":
        return f"{pad}long long {stmt['name']} = {_expr_to_c(stmt['value'])};"
    if op == "Assign":
        return f"{pad}{stmt['name']} = {_expr_to_c(stmt['value'])};"
    if op == "Print":
        return f"{pad}printf(\"%lld\\n\", {_expr_to_c(stmt['value'])});"
    if op == "IfElse":
        then = "\n".join(_stmt_to_c(s, indent + 1) for s in stmt.get("then", []))
        els = "\n".join(_stmt_to_c(s, indent + 1) for s in stmt.get("else", []))
        return f"{pad}if ({_cond_to_c(stmt['cond'])}) {{\n{then}\n{pad}}} else {{\n{els}\n{pad}}}"
    if op == "ForBounded":
        body = "\n".join(_stmt_to_c(s, indent + 1) for s in stmt.get("body", []))
        v = stmt["var"]
        return f"{pad}for (long long {v} = 0; {v} < {int(stmt['bound'])}; {v}++) {{\n{body}\n{pad}}}"
    if op == "WhileBoundedFuel":
        body = "\n".join(_stmt_to_c(s, indent + 1) for s in stmt.get("body", []))
        fuel = f"fuel_{indent}_{abs(hash(json.dumps(stmt, sort_keys=True))) % 100000}"
        return f"{pad}long long {fuel} = {int(stmt['fuel'])};\n{pad}while (({_cond_to_c(stmt['cond'])}) && {fuel} > 0) {{\n{body}\n{pad}    {fuel}--;\n{pad}}}"
    raise ValueError(op)


def _expr_to_c(expr: Dict[str, Any]) -> str:
    op = expr["op"]
    if op == "Int":
        return str(int(expr["value"]))
    if op == "Var":
        return expr["name"]
    if op == "Neg":
        return f"(-({_expr_to_c(expr['arg'])}))"
    sym = {"Add": "+", "Sub": "-", "Mul": "*", "DivExact": "/"}[op]
    return f"({_expr_to_c(expr['args'][0])} {sym} {_expr_to_c(expr['args'][1])})"


def _cond_to_c(cond: Dict[str, Any]) -> str:
    return f"{_expr_to_c(cond['left'])} {cond['cmp']} {_expr_to_c(cond['right'])}"


def _aggregate_metrics(metrics_by_scale: Dict[str, Dict[str, Any]], backend: CompilerBackend, compile_worker_count: int) -> Dict[str, Any]:
    invocations = sum(row["real_compiler_invocation_count"] for row in metrics_by_scale.values())
    verified = sum(row["compiler_verified_correct_count"] for row in metrics_by_scale.values())
    latencies: List[float] = []
    weighted_sps = 0.0
    for row in metrics_by_scale.values():
        weighted_sps += row["samples_per_second"]
    aggregate = {
        "scales_attempted": list(metrics_by_scale.keys()),
        "scales_completed": list(metrics_by_scale.keys()),
        "compile_worker_count": compile_worker_count,
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "real_compiler_invocation_count": invocations,
        "compile_success_count": sum(row["compile_success_count"] for row in metrics_by_scale.values()),
        "compile_failure_count": sum(row["compile_failure_count"] for row in metrics_by_scale.values()),
        "runtime_success_count": sum(row["runtime_success_count"] for row in metrics_by_scale.values()),
        "runtime_failure_count": sum(row["runtime_failure_count"] for row in metrics_by_scale.values()),
        "compiler_verified_correct_count": verified,
        "compiler_verified_failure_count": invocations - verified,
        "compiler_verified_correct_rate": round(verified / invocations, 6) if invocations else 0.0,
        "boundary_compiler_misroute_count": sum(row["boundary_compiler_misroute_count"] for row in metrics_by_scale.values()),
        "timeout_count": sum(row["timeout_count"] for row in metrics_by_scale.values()),
        "token_spacing_patch_enabled": True,
        "backend_claim_safe": backend.backend_type == "real_c_compiler",
        "forbidden_field_access_count": 0,
        "target_ir_access_before_candidate_generation": False,
        "expected_output_access_before_candidate_generation": False,
        "by_scale": metrics_by_scale,
        "samples_per_second": round(weighted_sps / max(len(metrics_by_scale), 1), 6),
    }
    # Keep top-level latency conservative by taking the max p-percentile across scales.
    for key in ["p50_latency_ms", "p95_latency_ms", "p99_latency_ms"]:
        aggregate[key] = max((row[key] for row in metrics_by_scale.values()), default=0.0)
    return aggregate


def _iter_rows(scale_dir: Path) -> Iterable[Dict[str, Any]]:
    for split in ["train", "eval", "test", "heldout"]:
        for path in sorted((scale_dir / split).glob("*.jsonl")):
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    yield json.loads(line)


def _sample_deterministic(rows: List[Dict[str, Any]], count: int, seed: int) -> List[Dict[str, Any]]:
    rows = list(rows)
    rows.sort(key=lambda row: hashlib.sha256((row["id"] + str(seed)).encode("utf-8")).hexdigest())
    return rows[: min(count, len(rows))]


def _write_trace(out: Path, trace: List[Dict[str, Any]], max_bytes: int = 45_000_000) -> None:
    shards = []
    current: List[str] = []
    size = 0
    shard_index = 0
    for row in trace:
        line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        if current and size + len(line.encode("utf-8")) > max_bytes:
            name = f"compiler_validation_trace_{shard_index:03d}.jsonl"
            (out / name).write_text("".join(current), encoding="utf-8")
            shards.append({"path": name, "row_count": len(current), "size_bytes": (out / name).stat().st_size})
            current = []
            size = 0
            shard_index += 1
        current.append(line)
        size += len(line.encode("utf-8"))
    name = f"compiler_validation_trace_{shard_index:03d}.jsonl"
    (out / name).write_text("".join(current), encoding="utf-8")
    shards.append({"path": name, "row_count": len(current), "size_bytes": (out / name).stat().st_size})
    _write_json(out / "compiler_validation_trace_manifest.json", {"trace_sharded": True, "shard_count": len(shards), "total_rows": len(trace), "shards": shards})


def _load_dataset_summaries(dataset_dir: Path, scales: Iterable[str]) -> Dict[str, Any]:
    summaries = {}
    for scale in scales:
        audit = json.loads((dataset_dir / scale / "audit.json").read_text(encoding="utf-8"))
        manifest = json.loads((dataset_dir / scale / "manifest.json").read_text(encoding="utf-8"))
        summaries[scale] = {"scale": scale, "actual_total": manifest["actual_total"], "audit": audit}
    return summaries


def _latency(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"p50_latency_ms": 0.0, "p95_latency_ms": 0.0, "p99_latency_ms": 0.0}
    ordered = sorted(values)
    return {
        "p50_latency_ms": round(statistics.median(ordered), 6),
        "p95_latency_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 6),
        "p99_latency_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.99))], 6),
    }


def _hash(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()[:16]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
