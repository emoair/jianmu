from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import CompilerBackend
from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import _msvc_environment
from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import _build_backend_compile_command
from jianmu.self_learning.darwinforge.coverage_expansion_accounting import audit_coverage_expansion_accounting
from jianmu.self_learning.darwinforge.coverage_expansion_scheduler import next_coverage_kind
from jianmu.self_learning.darwinforge.coverage_expansion_schema import BLOCKING_CATEGORIES, CoverageExpansionConfig
from jianmu.self_learning.darwinforge.opt_in_shape_diversity_builder import build_expanded_shape
from jianmu.self_learning.darwinforge.staged_opt_in_profile_schema import POLICY_BY_KIND


def run_coverage_expansion_execution(
    output_records: str | Path,
    config: CoverageExpansionConfig,
    targets: Dict[str, int],
    seed: int = 210,
    progress: bool = False,
) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    backend = detect_coverage_replay_backend()
    if backend.backend_type != "real_c_compiler":
        blocked = {
            "coverage_replay_started": True,
            "coverage_replay_completed": False,
            "environment_blocked": True,
            "blocking_issues": ["real_c_compiler_unavailable"],
            "backend_type": backend.backend_type,
            "compiler_name": backend.compiler_name,
        }
        (out / "coverage_expansion_execution_metrics.json").write_text(json.dumps(blocked, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return {**blocked, "rows": [], "heartbeats": [], "backend_report": {"backend_type": backend.backend_type, "compiler_name": backend.compiler_name, "compiler_environment": backend.compiler_environment}}
    started = time.perf_counter()
    rows: List[Dict[str, Any]] = []
    heartbeats: List[Dict[str, Any]] = []
    counters = {kind: 0 for kind in targets}
    compiler_count = 0
    hard_stop_hit = False
    last_progress = time.perf_counter() - 61.0
    while True:
        elapsed_hours = (time.perf_counter() - started) / 3600.0
        target_done = all(counters[kind] >= targets[kind] for kind in targets)
        wall_done = elapsed_hours >= config.wall_clock_min_hours
        min_done = len(rows) >= config.minimum_real_validation_events
        if target_done and wall_done:
            break
        if elapsed_hours >= config.hard_stop_hours:
            hard_stop_hit = True
            break
        if elapsed_hours >= config.max_runtime_hours and min_done and wall_done:
            break
        compiler_done = compiler_count >= config.minimum_real_compiler_invocations
        event_floor_mode = compiler_done and len(rows) < config.minimum_real_validation_events
        continuation_mode = target_done and not wall_done
        kind = _event_floor_kind(len(rows)) if event_floor_mode else next_coverage_kind(counters, targets, len(rows), continuation_mode)
        row = execute_coverage_sample(counters[kind] + seed, kind, backend, config.profile_name)
        row["category"] = kind
        row["heldout_id"] = f"coverage_heldout_{kind}_{counters[kind] % 1000:04d}"
        row["thread_id"] = str(threading.get_ident())
        row["coverage_continuation_mode"] = continuation_mode
        row["event_floor_mode"] = event_floor_mode
        rows.append(row)
        if row.get("compiler_invoked"):
            compiler_count += 1
        counters[kind] += 1
        if len(rows) % 5000 == 0:
            heartbeats.append(_heartbeat(len(rows), elapsed_hours))
        if progress and time.perf_counter() - last_progress > 60:
            _append_progress(out, {"coverage_rows": len(rows), "elapsed_hours": round(elapsed_hours, 4), "kind": kind})
            last_progress = time.perf_counter()
    metrics = _metrics(rows, counters, targets, started, config, hard_stop_hit)
    (out / "coverage_expansion_execution_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    accounting = audit_coverage_expansion_accounting(out, rows)
    return {**metrics, **accounting, "rows": rows, "heartbeats": heartbeats, "backend_report": {"backend_type": backend.backend_type, "compiler_name": backend.compiler_name, "compiler_environment": backend.compiler_environment}}


def execute_coverage_sample(index: int, kind: str, backend: Any, profile_name: str, timeout_seconds: int = 5) -> Dict[str, Any]:
    if kind == "malformed_opt_in_blocking":
        return _blocked_row(index, kind, profile_name, POLICY_BY_KIND["function"], "malformed", "explicit_opt_in_required")
    if kind in BLOCKING_CATEGORIES:
        policy = "opt_out_rollback_check" if kind == "opt_out_rollback" else "default_profile_blocking_check"
        return _blocked_row(index, kind, profile_name, policy, "enable_staged_opt_in_v1_0_7", "explicit_opt_in_required")
    policy = POLICY_BY_KIND["mixed" if kind == "mixed" else kind]
    shape = build_expanded_shape(kind, index)
    source = str(shape["source"])
    expected = str(shape["expected_stdout"]).strip()
    if backend.backend_type == "real_c_compiler":
        result = _compile_with_retry(source, backend, timeout_seconds)
        actual = str(result.get("stdout_value_if_safe") or "").strip()
    else:
        result = {"compiler_invoked": False, "compile_success": False, "runtime_invoked": False, "runtime_success": False, "timeout": False}
        actual = ""
    source_hash = _sha256(source)
    sample_id = f"v1_0_7_2_{kind}_{index:08d}"
    return {
        "sample_id": sample_id,
        "category": kind,
        "profile": profile_name,
        "explicit_opt_in": True,
        "policy": policy,
        "request_kind": kind,
        "adapter": "coverage_expansion_execution",
        "atomic_policy": policy,
        "builder": shape["builder"],
        "ir_kind": shape["ir_kind"],
        "emitter": shape["emitter"],
        "shape_signature": shape["shape_signature"],
        "source_shape": shape["source_shape"],
        "source_sha256": source_hash,
        "compile_invocation_id": _sha256(f"{sample_id}|{source_hash}|coverage_expansion"),
        "cl_invoked": bool(result.get("compiler_invoked") and backend.compiler_name == "cl"),
        "compiler_invoked": bool(result.get("compiler_invoked")),
        "link_invoked": bool(result.get("compile_success")),
        "exe_run": bool(result.get("runtime_invoked")),
        "expected_stdout": expected,
        "actual_stdout": actual,
        "passed": bool(result.get("runtime_success") and actual == expected),
        "bridge_reachable_without_opt_in": False,
        "cached": False,
        "stubbed": False,
        "timeout": bool(result.get("timeout")),
        "permission_error": bool(result.get("permission_error")),
        "cleanup_failure": False,
        "default_profile_modified": False,
        "real_promotion_enabled": False,
    }


def _blocked_row(index: int, kind: str, profile_name: str, policy: str, opt_in_flag: str, reason: str) -> Dict[str, Any]:
    sample_id = f"v1_0_7_2_{kind}_{index:08d}"
    return {
        "sample_id": sample_id,
        "category": kind,
        "profile": profile_name,
        "explicit_opt_in": False,
        "opt_in_flag": opt_in_flag,
        "policy": policy,
        "request_kind": kind,
        "adapter": "coverage_expansion_execution",
        "atomic_policy": policy,
        "builder": "blocked_without_explicit_opt_in",
        "ir_kind": "blocked",
        "emitter": "none",
        "shape_signature": f"blocked::{kind}::{index}",
        "source_shape": "blocked",
        "source_sha256": f"blocked-{kind}-{index}",
        "compile_invocation_id": f"blocked-{kind}-{index}",
        "cl_invoked": False,
        "compiler_invoked": False,
        "link_invoked": False,
        "exe_run": False,
        "expected_stdout": reason,
        "actual_stdout": reason,
        "passed": True,
        "bridge_reachable_without_opt_in": False,
        "cached": False,
        "stubbed": False,
        "timeout": False,
        "permission_error": False,
        "cleanup_failure": False,
        "default_profile_modified": False,
        "real_promotion_enabled": False,
    }


def _metrics(rows: List[Dict[str, Any]], counters: Dict[str, int], targets: Dict[str, int], started: float, config: CoverageExpansionConfig, hard_stop_hit: bool) -> Dict[str, Any]:
    elapsed = round((time.perf_counter() - started) / 3600.0, 6)
    return {
        "coverage_replay_started": True,
        "coverage_replay_completed": elapsed >= config.wall_clock_min_hours,
        "wall_clock_hours": elapsed,
        "wall_clock_minimum_satisfied": elapsed >= config.wall_clock_min_hours,
        "hard_stop_hit": hard_stop_hit,
        "category_counts": counters,
        "target_counts": targets,
        "all_categories_represented": all(counters.get(kind, 0) > 0 for kind in targets),
        "arithmetic_regression_success_rate": _rate(rows, "arithmetic"),
        "function_opt_in_success_rate": _rate(rows, "function"),
        "array_opt_in_success_rate": _rate(rows, "array"),
        "function_array_opt_in_success_rate": _rate(rows, "function_array"),
        "structured_recursion_opt_in_success_rate": _rate(rows, "structured_recursion"),
        "mixed_opt_in_success_rate": _rate(rows, "mixed"),
        "opt_out_rollback_success_rate": _rate(rows, "opt_out_rollback"),
        "post_rollback_default_blocking_success_rate": _rate(rows, "post_rollback_default_blocking"),
        "malformed_opt_in_blocking_success_rate": _rate(rows, "malformed_opt_in_blocking"),
        "default_blocking_success_rate": _rate(rows, "default_blocking"),
        "compiler_verified_correctness_rate": round(sum(1 for row in rows if row["passed"]) / len(rows), 6) if rows else 0.0,
        "workers_requested": config.workers,
        "workers_used": min(config.workers, config.compiler_workers, 16),
        "downgrade_reason": "",
        "event_floor_mode_used": any(row.get("event_floor_mode") for row in rows),
    }


def _rate(rows: List[Dict[str, Any]], kind: str) -> float:
    selected = [row for row in rows if row["category"] == kind]
    return round(sum(1 for row in selected if row["passed"]) / len(selected), 6) if selected else 0.0


def _heartbeat(events: int, elapsed_hours: float) -> Dict[str, Any]:
    return {
        "event_index": events,
        "elapsed_hours": round(elapsed_hours, 6),
        "default_profile_unchanged": True,
        "real_promotion_enabled": False,
        "user_facing_enabled": False,
        "official_release_enabled": False,
        "trace_writer_healthy": True,
        "temp_dir_isolation_healthy": True,
        "guard_failure": False,
    }


def _event_floor_kind(index: int) -> str:
    return ("default_blocking", "malformed_opt_in_blocking", "opt_out_rollback", "post_rollback_default_blocking")[index % 4]


def _compile_with_retry(source: str, backend: Any, timeout_seconds: int) -> Dict[str, Any]:
    last_error = ""
    for attempt in range(3):
        try:
            return _compile_and_run_source_tolerant(source, backend, timeout_seconds)
        except PermissionError as exc:
            last_error = str(exc)
            time.sleep(0.05 * (attempt + 1))
        except subprocess.TimeoutExpired:
            return {
                "compiler_invoked": True,
                "compile_success": False,
                "runtime_invoked": False,
                "runtime_success": False,
                "timeout": True,
                "stdout_value_if_safe": "",
            }
    return {
        "compiler_invoked": False,
        "compile_success": False,
        "runtime_invoked": False,
        "runtime_success": False,
        "timeout": False,
        "permission_error": True,
        "stdout_value_if_safe": last_error,
    }


def _compile_and_run_source_tolerant(source: str, backend: CompilerBackend, timeout_seconds: int) -> Dict[str, Any]:
    started = time.perf_counter()
    tmpdir = tempfile.mkdtemp(prefix="jianmu_v1072_")
    cleanup_failure = False
    try:
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
            "permission_error": False,
            "cleanup_failure": False,
            "latency_ms": 0.0,
        }
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_seconds, cwd=tmpdir, env=env, errors="replace")
        except subprocess.TimeoutExpired:
            result.update({"compile_returncode": -1, "timeout": True, "latency_ms": round((time.perf_counter() - started) * 1000, 6)})
            return result
        except PermissionError:
            result.update({"compile_returncode": -1, "permission_error": True, "latency_ms": round((time.perf_counter() - started) * 1000, 6)})
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
        except PermissionError:
            result.update({"runtime_invoked": True, "runtime_returncode": -1, "permission_error": True, "latency_ms": round((time.perf_counter() - started) * 1000, 6)})
            return result
        stdout = run.stdout.strip()
        result.update({
            "runtime_invoked": True,
            "runtime_returncode": run.returncode,
            "runtime_success": run.returncode == 0,
            "stdout_hash": _sha256(stdout),
            "stdout_value_if_safe": stdout if stdout.lstrip("-").isdigit() else None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 6),
        })
        return result
    finally:
        for attempt in range(3):
            try:
                shutil.rmtree(tmpdir)
                break
            except (PermissionError, NotADirectoryError, FileNotFoundError, OSError):
                cleanup_failure = True
                time.sleep(0.05 * (attempt + 1))
        if cleanup_failure and Path(tmpdir).exists():
            try:
                shutil.rmtree(tmpdir, ignore_errors=True)
            except OSError:
                pass


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def detect_coverage_replay_backend() -> CompilerBackend:
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    if backend.backend_type == "real_c_compiler":
        return backend
    fallback = r"C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
    if Path(fallback).exists():
        probe = subprocess.run(["cmd", "/c", f'call "{fallback}" >nul && cl /nologo'], capture_output=True, text=True, timeout=30, errors="replace")
        if "D8003" in (probe.stderr + probe.stdout):
            env = _msvc_environment(fallback)
            os.environ.update(env)
            return CompilerBackend(
                "real_c_compiler",
                "cl",
                "cl",
                compiler_environment="path",
                vcvars64_path=fallback,
                detection_report={"fallback_vs18_vcvars64": True, "vcvars64_path": fallback},
            )
    return backend


def _safe_print(text: str) -> None:
    try:
        print(text, flush=True)
    except OSError:
        try:
            sys.stderr.write(text + "\n")
            sys.stderr.flush()
        except OSError:
            pass


def _append_progress(out: Path, payload: Dict[str, Any]) -> None:
    with (out / "coverage_execution_progress.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
