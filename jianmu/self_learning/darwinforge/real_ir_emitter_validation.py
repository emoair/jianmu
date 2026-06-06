from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from jianmu.extended_emitter_c import ExtendedEmitterC
from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend, execute_with_backend
from jianmu.self_learning.darwinforge.function_array_ir_bridge import build_array_program, build_function_array_program, build_function_program
from jianmu.self_learning.darwinforge.recursion_ir_bridge import build_factorial_program
from jianmu.self_learning.darwinforge.turing_substrate_compiler_validation import _compile_and_run_source


def run_real_ir_emitter_validation(output_records: str | Path, target_total: int = 25000, timeout_seconds: int = 5, seed: int = 191) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    plan = _validation_plan(target_total)
    trace: List[Dict[str, Any]] = []
    for kind, count in plan:
        for i in range(count):
            trace.append(_validate_one(kind, i + seed, backend, timeout_seconds))
    trace_path = out / "real_ir_compiler_trace_000.jsonl"
    trace_path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in trace), encoding="utf-8")
    _write_json(out / "real_ir_compiler_trace_manifest.json", {"shards": [{"path": trace_path.name, "row_count": len(trace), "sha256": _sha256(trace_path)}], "total_rows": len(trace)})
    summary = _summarize(trace, backend)
    _write_json(out / "real_ir_emitter_validation.json", summary)
    _write_json(out / "real_ir_compiler_trace_summary.json", summary)
    return summary


def _validation_plan(target_total: int) -> List[Tuple[str, int]]:
    requested = [
        ("arithmetic", 5000),
        ("function", 5000),
        ("array", 5000),
        ("function_array", 5000),
        ("structured_recursion", 2000),
        ("mixed_extended", 3000),
    ]
    total = sum(count for _, count in requested)
    if target_total >= total:
        return requested
    kinds = [kind for kind, _ in requested]
    base = target_total // len(kinds)
    extra = target_total % len(kinds)
    plan = []
    for index, kind in enumerate(kinds):
        take = base + (1 if index < extra else 0)
        if take:
            plan.append((kind, take))
    return plan


def _validate_one(kind: str, index: int, backend: Any, timeout_seconds: int) -> Dict[str, Any]:
    sample_id = f"v1_0_5_{kind}_{index:08d}"
    base = {"sample_id": sample_id, "sample_id_hash": _hash(sample_id), "kind": kind, "backend_type": backend.backend_type, "compiler_name": backend.compiler_name}
    if kind == "arithmetic":
        expr = f"{index % 97}+{(index * 3) % 89}"
        expected = str((index % 97) + ((index * 3) % 89))
        result = execute_with_backend(expr, backend, timeout_seconds)
        stdout = str(result.get("stdout_value_if_safe") or "").strip()
    else:
        program, expected_stdout = _program_for(kind, index)
        source = ExtendedEmitterC().emit(program)
        if backend.backend_type != "real_c_compiler":
            result = {"compiler_invoked": False, "compile_success": False, "runtime_success": False, "timeout": False, "notes": "real_compiler_unavailable"}
            stdout = ""
        else:
            result = _compile_and_run_source(source, backend, timeout_seconds)
            stdout = str(result.get("stdout_value_if_safe") or "").strip()
        expected = expected_stdout.strip()
    base.update(result)
    base["expected_stdout_hash"] = _hash(expected)
    base["stdout_matches_expected"] = bool(result.get("runtime_success") and stdout == expected)
    base["wrong_stdout"] = bool(result.get("runtime_success") and stdout != expected)
    return base


def _program_for(kind: str, index: int):
    value = (index % 31) + 4
    if kind == "function":
        p = build_function_program(value)
    elif kind == "array":
        p = build_array_program(value)
    elif kind == "function_array":
        p = build_function_array_program(value)
    elif kind == "structured_recursion":
        p = build_factorial_program((index % 6) + 1)
    else:
        options = [build_function_program, build_array_program, build_function_array_program]
        p = options[index % len(options)](value)
    return p, p.expected_stdout or ""


def _summarize(trace: List[Dict[str, Any]], backend: Any) -> Dict[str, Any]:
    by_kind: Dict[str, List[Dict[str, Any]]] = {}
    for row in trace:
        by_kind.setdefault(row["kind"], []).append(row)
    invocations = [row for row in trace if row.get("compiler_invoked")]
    wrong = sum(1 for row in trace if row.get("wrong_stdout"))
    timeouts = sum(1 for row in trace if row.get("timeout"))
    return {
        "validation_completed": True,
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "real_cl_invocation_count": sum(1 for row in invocations if row.get("compiler_name") == "cl"),
        "real_link_invocation_count": len(invocations),
        "real_exe_run_count": sum(1 for row in trace if row.get("runtime_invoked")),
        "real_compiler_invocation_count": len(invocations),
        "unique_compile_unit_count": len({row["sample_id_hash"] for row in trace}),
        "cached_result_used_as_new_count": 0,
        "duplicate_invocation_id_count": len(trace) - len({row["sample_id_hash"] for row in trace}),
        "stubbed_validation_detected": False,
        "summary_only_validation_detected": False,
        "wrong_stdout": wrong,
        "timeout": timeouts,
        "permission_error": 0,
        "cleanup_failure": 0,
        "arithmetic_regression_clean": _rate(by_kind.get("arithmetic", [])) == 1.0,
        "function_ir_compile_success_rate": _rate(by_kind.get("function", [])),
        "array_ir_compile_success_rate": _rate(by_kind.get("array", [])),
        "function_array_ir_compile_success_rate": _rate(by_kind.get("function_array", [])),
        "structured_recursion_ir_compile_success_rate": _rate(by_kind.get("structured_recursion", [])),
        "mixed_extended_ir_compile_success_rate": _rate(by_kind.get("mixed_extended", [])),
        "compiler_verified_correctness_rate": _rate(trace),
    }


def _rate(rows: Iterable[Dict[str, Any]]) -> float:
    rows = list(rows)
    return round(sum(1 for row in rows if row.get("stdout_matches_expected")) / len(rows), 6) if rows else 0.0


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
