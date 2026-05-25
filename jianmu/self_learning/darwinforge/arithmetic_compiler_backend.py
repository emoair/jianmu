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
import shutil

from jianmu.sandbox import build_compile_command, detect_supported_c_compiler


SAFE_EXPRESSION_RE = re.compile(r"^[0-9+\-*/()\s]+$")
_MSVC_ENV_CACHE: Dict[str, str] | None = None


@dataclass(frozen=True)
class CompilerBackend:
    backend_type: str
    compiler_path: str
    compiler_name: str
    compiler_environment: str = ""
    vcvars64_path: str = ""
    detection_report: Dict[str, Any] | None = None

    @property
    def compiler_available(self) -> bool:
        return self.backend_type == "real_c_compiler"


def detect_arithmetic_backend(prefer_python_subprocess: bool = True, prefer_msvc: bool = False) -> CompilerBackend:
    report = detect_msvc_and_path_compilers()
    if prefer_msvc and report["cl_bv_test_passed"]:
        return CompilerBackend(
            "real_c_compiler",
            "cl",
            "cl",
            compiler_environment="msvc_vcvars64",
            vcvars64_path=report["vcvars64_path"],
            detection_report=report,
        )
    compiler_path, compiler_name = detect_supported_c_compiler()
    if compiler_path and compiler_name:
        return CompilerBackend("real_c_compiler", compiler_path, compiler_name, compiler_environment="path", detection_report=report)
    if report["cl_bv_test_passed"]:
        return CompilerBackend(
            "real_c_compiler",
            "cl",
            "cl",
            compiler_environment="msvc_vcvars64",
            vcvars64_path=report["vcvars64_path"],
            detection_report=report,
        )
    if prefer_python_subprocess:
        return CompilerBackend("python_subprocess_executor", "", "", compiler_environment="python_subprocess", detection_report=report)
    return CompilerBackend("unavailable", "", "", detection_report=report)


def detect_msvc_and_path_compilers(timeout_seconds: int = 15) -> Dict[str, Any]:
    vswhere = Path(r"C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe")
    path_cl = shutil.which("cl")
    path_gcc = shutil.which("gcc")
    path_clang = shutil.which("clang")
    report: Dict[str, Any] = {
        "os_name": os.name,
        "path_cl_found": bool(path_cl),
        "path_gcc_found": bool(path_gcc),
        "path_clang_found": bool(path_clang),
        "vswhere_found": vswhere.exists(),
        "vcvars64_found": False,
        "vcvars64_path": "",
        "cl_bv_test_passed": False,
        "cl_version_text_tail": "",
        "detection_conclusion": "no_c_compiler_detected",
    }
    if path_cl:
        proc = _run_cl_bv(None, timeout_seconds)
        report["cl_bv_test_passed"] = _cl_bv_looks_available(proc)
        report["cl_version_text_tail"] = _tail(proc.stdout + proc.stderr)
        report["detection_conclusion"] = "path_cl_available" if report["cl_bv_test_passed"] else "path_cl_found_but_failed"
        return report
    if path_gcc:
        report["detection_conclusion"] = "path_gcc_available"
    if path_clang:
        report["detection_conclusion"] = "path_clang_available"
    if not vswhere.exists():
        return report
    cmd = [
        str(vswhere),
        "-latest",
        "-products",
        "*",
        "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64",
        "-find",
        r"VC\Auxiliary\Build\vcvars64.bat",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
    except (OSError, subprocess.TimeoutExpired) as exc:
        report["detection_conclusion"] = f"vswhere_failed: {type(exc).__name__}"
        return report
    candidates = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    vcvars = candidates[0] if candidates else ""
    report["vcvars64_found"] = bool(vcvars and Path(vcvars).exists())
    report["vcvars64_path"] = vcvars if report["vcvars64_found"] else ""
    if not report["vcvars64_found"]:
        report["detection_conclusion"] = "vswhere_found_no_vcvars64"
        return report
    cl_proc = _run_cl_bv(report["vcvars64_path"], timeout_seconds)
    report["cl_bv_test_passed"] = _cl_bv_looks_available(cl_proc)
    report["cl_version_text_tail"] = _tail(cl_proc.stdout + cl_proc.stderr)
    report["detection_conclusion"] = "msvc_vcvars64_cl_available" if report["cl_bv_test_passed"] else "vcvars64_found_but_cl_failed"
    return report


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
        compile_cmd, compile_env = _build_backend_compile_command(backend, src, exe)
        compile_hash = _hash_command(compile_cmd)
        try:
            compile_proc = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=tmpdir,
                env=compile_env,
                errors="replace",
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
        "compiler_environment": backend.compiler_environment,
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


def _build_backend_compile_command(backend: CompilerBackend, src: Path, exe: Path) -> tuple[list[str], Dict[str, str] | None]:
    if backend.compiler_environment == "msvc_vcvars64":
        obj = exe.with_suffix(".obj")
        env = _msvc_environment(backend.vcvars64_path)
        search_path = env.get("PATH") or env.get("Path") or ""
        compiler = shutil.which("cl", path=search_path) or "cl"
        return [compiler, "/nologo", "/TC", src.name, f"/Fe:{exe.name}", f"/Fo:{obj.name}"], env
    return build_compile_command(backend.compiler_path, backend.compiler_name, src, exe), None


def _msvc_environment(vcvars64_path: str) -> Dict[str, str]:
    global _MSVC_ENV_CACHE
    if _MSVC_ENV_CACHE is not None:
        return _MSVC_ENV_CACHE
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = Path(tmpdir) / "env.txt"
        batch = Path(tmpdir) / "capture_msvc_env.bat"
        batch.write_text("\n".join([
            "@echo off",
            f'call "{vcvars64_path}" >nul',
            f'set > "{env_file}"',
            "",
        ]), encoding="utf-8")
        subprocess.run([str(batch)], capture_output=True, text=True, timeout=60, errors="replace")
        env = dict(os.environ)
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    env[key] = value
        if "Path" in env:
            env["PATH"] = env["Path"]
        elif "PATH" in env:
            env["Path"] = env["PATH"]
        _MSVC_ENV_CACHE = env
        return env


def _run_cl_bv(vcvars64_path: str | None, timeout_seconds: int) -> subprocess.CompletedProcess[str]:
    if vcvars64_path:
        with tempfile.TemporaryDirectory() as tmpdir:
            batch = Path(tmpdir) / "cl_bv_test.bat"
            batch.write_text("\n".join([
                "@echo off",
                f'call "{vcvars64_path}" >nul',
                "cl /Bv",
                "",
            ]), encoding="utf-8")
            try:
                return subprocess.run([str(batch)], capture_output=True, text=True, timeout=timeout_seconds, errors="replace")
            except (OSError, subprocess.TimeoutExpired) as exc:
                return subprocess.CompletedProcess([str(batch)], -1, "", str(exc))
    else:
        cmd = ["cmd", "/d", "/s", "/c", "cl /Bv"] if os.name == "nt" else ["cl", "/Bv"]
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return subprocess.CompletedProcess(cmd, -1, "", str(exc))


def _tail(text: str, max_chars: int = 2000) -> str:
    return text[-max_chars:]


def _cl_bv_looks_available(proc: subprocess.CompletedProcess[str]) -> bool:
    text = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode == 0 or "C/C++" in text or "Compiler" in text or "cl.exe" in text
