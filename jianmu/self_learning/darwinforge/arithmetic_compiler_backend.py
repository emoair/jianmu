from __future__ import annotations

import hashlib
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from jianmu.sandbox import build_compile_command, detect_supported_c_compiler


SAFE_EXPRESSION_RE = re.compile(r"^[0-9+\-*/()\s]+$")


@dataclass(frozen=True)
class CompilerBackend:
    backend_type: str
    compiler_path: str
    compiler_name: str

    @property
    def compiler_available(self) -> bool:
        return self.backend_type == "real_c_compiler"


def detect_arithmetic_backend(prefer_python_subprocess: bool = True) -> CompilerBackend:
    compiler_path, compiler_name = detect_supported_c_compiler()
    if compiler_path and compiler_name:
        return CompilerBackend("real_c_compiler", compiler_path, compiler_name)
    if prefer_python_subprocess:
        return CompilerBackend("python_subprocess_executor", "", "")
    return CompilerBackend("unavailable", "", "")


def is_safe_c_arithmetic_expression(expression: str) -> bool:
    text = expression.strip()
    if not text:
        return False
    if not SAFE_EXPRESSION_RE.fullmatch(text):
        return False
    forbidden = [";", ",", "#", "=", "<", ">", "&", "|", "^", "%", "[", "]", "{", "}"]
    return not any(token in text for token in forbidden)


def generate_safe_c_program(expression: str) -> str:
    if not is_safe_c_arithmetic_expression(expression):
        raise ValueError("unsafe arithmetic expression")
    return "\n".join([
        "#include <stdio.h>",
        "",
        "int main(void) {",
        f"    long long result = (long long)({expression});",
        "    printf(\"%lld\\n\", result);",
        "    return 0;",
        "}",
        "",
    ])


def execute_with_backend(expression: str, backend: CompilerBackend, timeout_seconds: int = 5) -> Dict[str, Any]:
    started = time.perf_counter()
    if not is_safe_c_arithmetic_expression(expression):
        return _base_result(backend, started, unsafe_expression=True, notes="unsafe_expression")
    if backend.backend_type == "real_c_compiler":
        return _execute_c_compiler(expression, backend, timeout_seconds, started)
    if backend.backend_type == "python_subprocess_executor":
        return _execute_python_subprocess(expression, backend, timeout_seconds, started)
    result = _base_result(backend, started)
    result["notes"] = "backend_unavailable"
    return result


def _execute_c_compiler(expression: str, backend: CompilerBackend, timeout_seconds: int, started: float) -> Dict[str, Any]:
    program = generate_safe_c_program(expression)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        src = tmp_path / "prog.c"
        exe = tmp_path / ("prog.exe" if os.name == "nt" else "prog")
        src.write_text(program, encoding="utf-8")
        compile_cmd = build_compile_command(backend.compiler_path, backend.compiler_name, src, exe)
        compile_hash = _hash_command(compile_cmd)
        try:
            compile_proc = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=tmpdir,
            )
        except subprocess.TimeoutExpired:
            result = _base_result(backend, started)
            result.update({
                "compiler_command_hash": compile_hash,
                "compiler_invoked": True,
                "compile_returncode": -1,
                "timeout": True,
                "notes": "compile_timeout",
            })
            return result
        result = _base_result(backend, started)
        result.update({
            "compiler_command_hash": compile_hash,
            "compiler_invoked": True,
            "compile_returncode": compile_proc.returncode,
            "compile_success": compile_proc.returncode == 0,
        })
        if compile_proc.returncode != 0:
            result["notes"] = "compile_error"
            return result
        try:
            run_proc = subprocess.run(
                [str(exe)],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=tmpdir,
            )
        except subprocess.TimeoutExpired:
            result.update({
                "runtime_invoked": True,
                "runtime_returncode": -1,
                "timeout": True,
                "notes": "runtime_timeout",
                "latency_ms": round((time.perf_counter() - started) * 1000, 6),
            })
            return result
        stdout = run_proc.stdout.strip()
        result.update({
            "runtime_invoked": True,
            "runtime_returncode": run_proc.returncode,
            "runtime_success": run_proc.returncode == 0,
            "stdout_hash": _hash_text(stdout),
            "stdout_value_if_safe": stdout if _safe_stdout(stdout) else None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 6),
        })
        return result


def _execute_python_subprocess(expression: str, backend: CompilerBackend, timeout_seconds: int, started: float) -> Dict[str, Any]:
    code = (
        "from jianmu.self_learning.darwinforge.arithmetic_safe_evaluator import safe_evaluate_expression;"
        "import sys;"
        "value,_=safe_evaluate_expression(sys.argv[1]);"
        "print(value)"
    )
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code, expression],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        result = _base_result(backend, started)
        result.update({"runtime_invoked": True, "timeout": True, "runtime_returncode": -1, "notes": "python_subprocess_timeout"})
        return result
    stdout = proc.stdout.strip()
    result = _base_result(backend, started)
    result.update({
        "runtime_invoked": True,
        "runtime_returncode": proc.returncode,
        "runtime_success": proc.returncode == 0,
        "stdout_hash": _hash_text(stdout),
        "stdout_value_if_safe": stdout if _safe_stdout(stdout) else None,
        "latency_ms": round((time.perf_counter() - started) * 1000, 6),
    })
    return result


def latency_summary(values: list[float]) -> Dict[str, float]:
    if not values:
        return {"p50_latency_ms": 0.0, "p95_latency_ms": 0.0, "p99_latency_ms": 0.0}
    ordered = sorted(values)
    return {
        "p50_latency_ms": round(statistics.median(ordered), 6),
        "p95_latency_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 6),
        "p99_latency_ms": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.99))], 6),
    }


def _base_result(backend: CompilerBackend, started: float, unsafe_expression: bool = False, notes: str = "") -> Dict[str, Any]:
    return {
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_command_hash": None,
        "compiler_invoked": False,
        "compile_returncode": None,
        "compile_success": False,
        "runtime_invoked": False,
        "runtime_returncode": None,
        "runtime_success": False,
        "stdout_hash": None,
        "stdout_value_if_safe": None,
        "timeout": False,
        "unsafe_expression": unsafe_expression,
        "latency_ms": round((time.perf_counter() - started) * 1000, 6),
        "notes": notes,
    }


def _hash_command(command: list[Any]) -> str:
    return _hash_text(subprocess.list2cmdline([str(part) for part in command]))


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _safe_stdout(text: str) -> bool:
    return bool(re.fullmatch(r"-?\d+", text.strip()))
