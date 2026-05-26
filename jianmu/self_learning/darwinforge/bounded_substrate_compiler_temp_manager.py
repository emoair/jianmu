from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
import traceback
import uuid
from pathlib import Path
from typing import Any, Dict

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import CompilerBackend, _build_backend_compile_command, detect_arithmetic_backend
from jianmu.self_learning.darwinforge.turing_substrate_compiler_validation import target_ir_to_c_source


def make_sample_temp_dir(root: str | Path, run_id: str, worker_id: int, sample_id_hash: str) -> Path:
    safe_hash = "".join(ch for ch in sample_id_hash if ch.isalnum() or ch in "-_")[:32]
    # Keep compiler temp files outside the OneDrive-backed records tree. The
    # audit output still lives under records/, but cl.exe/link.exe intermediates
    # use the local temp volume to avoid sync-provider handle races.
    temp_root = Path(tempfile.gettempdir()) / "jianmu_v0_9_7_2_compiler_tmp"
    path = temp_root / run_id / f"worker_{worker_id}" / f"{safe_hash}_{uuid.uuid4().hex[:12]}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def validate_sample_with_temp_manager(
    row: Dict[str, Any],
    output_records: str | Path,
    run_id: str,
    worker_id: int,
    timeout_seconds: int = 5,
    backend: CompilerBackend | None = None,
) -> Dict[str, Any]:
    backend = backend or detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    sample_hash = _hash(row.get("id", row.get("sample_id_hash", "")))
    temp_dir = make_sample_temp_dir(output_records, run_id, worker_id, sample_hash)
    c_path = temp_dir / "program.c"
    obj_path = temp_dir / "program.obj"
    exe_path = temp_dir / "program.exe"
    started = time.perf_counter()
    result: Dict[str, Any] = {
        "sample_id_hash": sample_hash,
        "worker_id": worker_id,
        "temp_dir_hash": _hash(str(temp_dir)),
        "c_path_hash": _hash(str(c_path)),
        "obj_path_hash": _hash(str(obj_path)),
        "exe_path_hash": _hash(str(exe_path)),
        "path_length": len(str(exe_path)),
        "path_has_spaces": " " in str(exe_path),
        "path_has_unicode": any(ord(ch) > 127 for ch in str(exe_path)),
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "compiler_invoked": False,
        "c_file_exists_before_compile": False,
        "obj_file_exists_after_compile": False,
        "exe_file_exists_after_compile": False,
        "exe_file_exists_before_run": False,
        "compile_returncode": None,
        "runtime_returncode": None,
        "compile_success": False,
        "runtime_success": False,
        "stdout_hash": None,
        "expected_output_hash": _hash(row.get("expected_output") or ""),
        "compiler_verified_correct": False,
        "permission_error_stage": "none",
        "exception_type": "",
        "exception_message_tail": "",
        "traceback_tail": "",
        "cleanup_attempted": False,
        "cleanup_success": False,
        "cleanup_permission_error": False,
        "cleanup_retry_count": 0,
        "cleanup_failure_count": 0,
        "compile_stdout_tail": "",
        "compile_stderr_tail": "",
        "runtime_stdout_tail": "",
        "runtime_stderr_tail": "",
        "timeout": False,
        "latency_ms": 0.0,
        "notes": "",
    }
    try:
        if backend.backend_type != "real_c_compiler":
            result["notes"] = "real_compiler_unavailable"
            return result
        try:
            source = target_ir_to_c_source(row["target_ir"])
            c_path.write_text(source, encoding="utf-8")
        except PermissionError as exc:
            _record_exception(result, "permission_write_c_source", exc)
            return result
        result["c_file_exists_before_compile"] = c_path.exists()
        try:
            cmd, env = _build_backend_compile_command(backend, c_path, exe_path)
            cmd = _patch_compile_command(cmd, obj_path)
            result["compiler_invoked"] = True
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds, cwd=str(temp_dir), env=env, errors="replace")
        except PermissionError as exc:
            _record_exception(result, "permission_compile_spawn", exc)
            return result
        except subprocess.TimeoutExpired as exc:
            result.update({"timeout": True, "compile_returncode": -1, "exception_type": type(exc).__name__, "permission_error_stage": "compile_wait"})
            return result
        result.update({
            "compile_returncode": proc.returncode,
            "compile_success": proc.returncode == 0,
            "compile_stdout_tail": (proc.stdout or "")[-1000:],
            "compile_stderr_tail": (proc.stderr or "")[-1000:],
            "obj_file_exists_after_compile": obj_path.exists(),
            "exe_file_exists_after_compile": exe_path.exists(),
        })
        if proc.returncode != 0:
            result["permission_error_stage"] = "compile_wait"
            return result
        result["exe_file_exists_before_run"] = exe_path.exists()
        run = None
        for attempt, delay in enumerate((0.0, 0.05, 0.1, 0.2)):
            if delay:
                time.sleep(delay)
            try:
                run = subprocess.run([str(exe_path)], capture_output=True, text=True, timeout=timeout_seconds, cwd=str(temp_dir), errors="replace")
                if attempt:
                    result["notes"] = f"run_exe_permission_retry_count={attempt}"
                break
            except PermissionError as exc:
                _record_exception(result, "permission_run_exe", exc)
                result["run_exe_permission_retry_count"] = attempt + 1
                continue
            except subprocess.TimeoutExpired as exc:
                result.update({"timeout": True, "runtime_returncode": -1, "exception_type": type(exc).__name__, "permission_error_stage": "run_exe_wait"})
                return result
        if run is None:
            return result
        stdout = (run.stdout or "").strip()
        expected = (row.get("expected_output") or "").strip()
        result.update({
            "runtime_returncode": run.returncode,
            "runtime_success": run.returncode == 0,
            "runtime_stdout_tail": (run.stdout or "")[-1000:],
            "runtime_stderr_tail": (run.stderr or "")[-1000:],
            "stdout_hash": _hash(stdout),
            "compiler_verified_correct": run.returncode == 0 and stdout == expected,
        })
        if run.returncode != 0:
            result["permission_error_stage"] = "run_exe_wait"
        elif stdout != expected:
            result["permission_error_stage"] = "wrong_output"
        return result
    except Exception as exc:  # defensive: taxonomy needs a trace, not a crash.
        _record_exception(result, "unknown", exc)
        return result
    finally:
        result["latency_ms"] = round((time.perf_counter() - started) * 1000, 6)
        cleanup = cleanup_temp_dir(temp_dir)
        result["cleanup_attempted"] = True
        result["cleanup_success"] = cleanup["cleanup_success"]
        result["cleanup_permission_error"] = cleanup["cleanup_permission_error"]
        result["cleanup_retry_count"] = cleanup["cleanup_retry_count"]
        result["cleanup_failure_count"] = 0 if cleanup["cleanup_success"] else 1
        if cleanup["cleanup_permission_error"] and result["permission_error_stage"] == "none":
            result["permission_error_stage"] = "permission_cleanup_temp_dir"
            result["notes"] = "verification completed; cleanup PermissionError recorded separately"


def cleanup_temp_dir(path: str | Path, retries: tuple[float, ...] = (0.05, 0.1, 0.2)) -> Dict[str, Any]:
    temp = Path(path)
    attempted = 0
    for delay in (0.0, *retries):
        if delay:
            time.sleep(delay)
        attempted += 1
        try:
            shutil.rmtree(temp, ignore_errors=False)
            return {"cleanup_success": True, "cleanup_permission_error": False, "cleanup_retry_count": attempted - 1}
        except PermissionError:
            continue
        except FileNotFoundError:
            return {"cleanup_success": True, "cleanup_permission_error": False, "cleanup_retry_count": attempted - 1}
        except OSError:
            continue
    return {"cleanup_success": False, "cleanup_permission_error": True, "cleanup_retry_count": attempted - 1}


def _patch_compile_command(cmd: list[str], obj_path: Path) -> list[str]:
    patched = list(cmd)
    if patched and Path(patched[0]).name.lower() == "cl.exe" or (patched and patched[0].lower() == "cl"):
        if not any(part.startswith("/Fo") for part in patched):
            patched.insert(1, f"/Fo:{obj_path}")
        if "/nologo" not in patched:
            patched.insert(1, "/nologo")
    return patched


def _record_exception(result: Dict[str, Any], stage: str, exc: BaseException) -> None:
    result["permission_error_stage"] = stage
    result["exception_type"] = type(exc).__name__
    result["exception_message_tail"] = str(exc)[-500:]
    result["traceback_tail"] = traceback.format_exc()[-2000:]


def _hash(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:16]
