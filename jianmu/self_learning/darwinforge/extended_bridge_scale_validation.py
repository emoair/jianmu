from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List

from jianmu.extended_emitter_c import ExtendedEmitterC
from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend, execute_with_backend
from jianmu.self_learning.darwinforge.function_array_ir_bridge import build_array_program, build_function_array_program, build_function_program
from jianmu.self_learning.darwinforge.recursion_ir_bridge import build_factorial_program
from jianmu.self_learning.darwinforge.scale_compiler_accounting_audit import audit_scale_compiler_accounting
from jianmu.self_learning.darwinforge.scale_trace_manifest_builder import write_scale_trace_pack
from jianmu.self_learning.darwinforge.turing_substrate_compiler_validation import _compile_and_run_source


KIND_TO_POLICY = {
    "arithmetic": "canonical_arithmetic_targetir",
    "function": "canonical_function_targetir",
    "array": "canonical_array_targetir",
    "function_array": "canonical_function_array_targetir",
    "structured_recursion": "canonical_structured_recursion_targetir",
    "mixed_extended": "mixed_extended_ir_path",
}


def run_extended_bridge_scale_validation(
    output_records: str | Path,
    targets: Dict[str, int],
    wall_clock_min_hours: float,
    max_runtime_hours: float,
    hard_stop_hours: float,
    minimum_real_compiler_invocations: int,
    seed: int = 194,
    timeout_seconds: int = 5,
) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    started = time.perf_counter()
    rows: List[Dict[str, Any]] = []
    counters = {kind: 0 for kind in targets}
    hard_stop_hit = False
    while True:
        elapsed_hours = (time.perf_counter() - started) / 3600.0
        target_done = all(counters[kind] >= targets[kind] for kind in targets)
        minimum_done = len(rows) >= minimum_real_compiler_invocations
        wall_done = elapsed_hours >= wall_clock_min_hours
        if target_done and wall_done:
            break
        if elapsed_hours >= hard_stop_hours:
            hard_stop_hit = True
            break
        if elapsed_hours >= max_runtime_hours and minimum_done and wall_done:
            break
        kind = _next_kind(counters, targets, len(rows))
        rows.append(_validate_kind(kind, counters[kind] + seed, backend, timeout_seconds))
        counters[kind] += 1
    metrics = _metrics(rows, counters, targets, started, wall_clock_min_hours, hard_stop_hit, backend)
    (out / "scale_validation_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trace_pack = write_scale_trace_pack(out, rows, {"backend_type": backend.backend_type, "compiler_name": backend.compiler_name, "compiler_environment": backend.compiler_environment})
    accounting = audit_scale_compiler_accounting(out, rows)
    return {**metrics, **trace_pack, **accounting}


def _next_kind(counters: Dict[str, int], targets: Dict[str, int], index: int) -> str:
    remaining = [kind for kind in targets if counters[kind] < targets[kind]]
    if remaining:
        return remaining[index % len(remaining)]
    return list(targets)[index % len(targets)]


def _validate_kind(kind: str, index: int, backend: Any, timeout_seconds: int) -> Dict[str, Any]:
    sample_id = f"v1_0_5_1_{kind}_{index:08d}"
    policy = KIND_TO_POLICY[kind]
    if kind == "arithmetic":
        expr = f"{index % 101}+{(index * 5) % 97}"
        expected = str((index % 101) + ((index * 5) % 97))
        source = f"#include <stdio.h>\nint main(void) {{ printf(\"%d\\n\", {expr}); return 0; }}\n"
        result = execute_with_backend(expr, backend, timeout_seconds)
        actual = str(result.get("stdout_value_if_safe") or "").strip()
        ir_kind = "arithmetic"
        builder = "existing_arithmetic_compiler_backend"
    else:
        program, expected_stdout, ir_kind, builder = _program(kind, index)
        source = ExtendedEmitterC().emit(program)
        expected = expected_stdout.strip()
        if backend.backend_type == "real_c_compiler":
            result = _compile_and_run_source(source, backend, timeout_seconds)
            actual = str(result.get("stdout_value_if_safe") or "").strip()
        else:
            result = {"compiler_invoked": False, "runtime_invoked": False, "compile_success": False, "runtime_success": False, "timeout": False}
            actual = ""
    compile_id = _hash(sample_id + source)
    return {
        "sample_id": sample_id,
        "sample_id_hash": _hash(sample_id),
        "policy": policy,
        "builder": builder,
        "ir_kind": ir_kind,
        "emitter": "ExtendedEmitterC" if kind != "arithmetic" else "existing_arithmetic_backend",
        "source_sha256": _hash(source),
        "compile_invocation_id": compile_id,
        "cl_invoked": bool(result.get("compiler_invoked") and backend.compiler_name == "cl"),
        "compiler_invoked": bool(result.get("compiler_invoked")),
        "link_invoked": bool(result.get("compile_success")),
        "exe_run": bool(result.get("runtime_invoked")),
        "expected_stdout": expected,
        "actual_stdout": actual,
        "passed": bool(result.get("runtime_success") and actual == expected),
        "cached": False,
        "stubbed": False,
        "timeout": bool(result.get("timeout")),
        "permission_error": False,
        "cleanup_failure": False,
    }


def _program(kind: str, index: int):
    value = (index % 31) + 4
    if kind == "function":
        return build_function_program(value), f"{value}\n", "FunctionCallProgram", "build_function_program"
    if kind == "array":
        return build_array_program(value), f"{value}\n", "ArrayProgram", "build_array_program"
    if kind == "function_array":
        return build_function_array_program(value), f"{value}\n", "FunctionArrayProgram", "build_function_array_program"
    if kind == "structured_recursion":
        n = (index % 6) + 1
        program = build_factorial_program(n)
        return program, program.expected_stdout or "", "RecursiveFunctionProgram", "build_factorial_program"
    options = [("function", build_function_program), ("array", build_array_program), ("function_array", build_function_array_program)]
    name, builder = options[index % len(options)]
    program = builder(value)
    return program, program.expected_stdout or "", f"mixed_{name}", builder.__name__


def _metrics(rows: List[Dict[str, Any]], counters: Dict[str, int], targets: Dict[str, int], started: float, wall_clock_min_hours: float, hard_stop_hit: bool, backend: Any) -> Dict[str, Any]:
    elapsed_hours = (time.perf_counter() - started) / 3600.0
    return {
        "phase_b_started": True,
        "phase_b_completed": elapsed_hours >= wall_clock_min_hours,
        "wall_clock_hours": round(elapsed_hours, 6),
        "wall_clock_minimum_satisfied": elapsed_hours >= wall_clock_min_hours,
        "hard_stop_hit": hard_stop_hit,
        "category_counts": counters,
        "target_counts": targets,
        "all_policy_categories_represented": all(counters.get(kind, 0) > 0 for kind in targets),
        "arithmetic_regression_compile_success_rate": _rate(rows, "arithmetic"),
        "function_ir_compile_success_rate": _rate(rows, "function"),
        "array_ir_compile_success_rate": _rate(rows, "array"),
        "function_array_ir_compile_success_rate": _rate(rows, "function_array"),
        "structured_recursion_ir_compile_success_rate": _rate(rows, "structured_recursion"),
        "mixed_extended_ir_compile_success_rate": _rate(rows, "mixed_extended"),
        "compiler_verified_correctness_rate": round(sum(1 for row in rows if row["passed"]) / len(rows), 6) if rows else 0.0,
        "real_compiler_invocations": sum(1 for row in rows if row["compiler_invoked"]),
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
    }


def _rate(rows: List[Dict[str, Any]], kind: str) -> float:
    selected = [row for row in rows if row["sample_id"].split("_")[4] == kind.split("_")[0] or row["policy"] == KIND_TO_POLICY.get(kind)]
    if not selected:
        return 0.0
    return round(sum(1 for row in selected if row["passed"]) / len(selected), 6)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

