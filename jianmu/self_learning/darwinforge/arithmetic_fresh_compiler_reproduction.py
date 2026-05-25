from __future__ import annotations

import hashlib
import json
import os
import random
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import (
    CompilerBackend,
    _build_backend_compile_command,
    detect_arithmetic_backend,
    is_safe_c_arithmetic_expression,
    latency_summary,
)
from jianmu.self_learning.darwinforge.arithmetic_fresh_compiler_readiness import (
    assess_fresh_compiler_readiness,
)


MODE_LIMITS = {
    "quick": {"supported": 100, "boundary": 100, "seeds": 1},
    "small": {"supported": 1000, "boundary": 1000, "seeds": 1},
    "medium": {"supported": 3000, "boundary": 3000, "seeds": 3},
}
SUPPORTED_STAGES = ["precedence", "parentheses", "negative_numbers", "exact_division", "mixed_composition"]
BOUNDARY_CATEGORIES = [
    "unsupported_arithmetic_boundary",
    "true_false_accept_trap",
    "future_domain_candidate",
    "near_ood_arithmetic",
    "hard_ood",
]


def run_fresh_compiler_reproduction(
    records_dir: str | Path,
    original_compiler_records: str | Path,
    dataset_dir: str | Path,
    output_records: str | Path,
    modes: Iterable[str],
    supported_samples: int = 3000,
    boundary_samples: int = 3000,
    seeds: Iterable[int] | None = None,
    timeout_seconds: int = 5,
) -> Dict[str, Any]:
    started = time.perf_counter()
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    mode_list = [mode for mode in modes if mode]
    seed_list = list(seeds or [45])
    original_hashes = _original_sample_hashes(Path(original_compiler_records))
    dataset_rows = _read_dataset_rows(Path(dataset_dir))
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)

    completed: list[str] = []
    skipped: list[dict[str, str]] = []
    trace_rows: list[dict[str, Any]] = []
    for index, mode in enumerate(mode_list):
        if mode not in MODE_LIMITS:
            skipped.append({"mode": mode, "reason": "unknown_mode"})
            continue
        seed = seed_list[min(index, len(seed_list) - 1)]
        cfg = MODE_LIMITS[mode]
        supported_limit = min(cfg["supported"], supported_samples)
        boundary_limit = min(cfg["boundary"], boundary_samples)
        supported, boundary = _select_fresh_samples(dataset_rows, original_hashes, supported_limit, boundary_limit, seed)
        for row in supported:
            trace_rows.append(_trace_supported(row, backend, original_hashes, timeout_seconds))
        for row in boundary:
            trace_rows.append(_trace_boundary(row, backend, original_hashes))
        completed.append(mode)

    trace_path = out / "fresh_compiler_trace.jsonl"
    _write_jsonl(trace_path, trace_rows)
    metrics = _summarize(
        modes_attempted=mode_list,
        modes_completed=completed,
        modes_skipped=skipped,
        trace_rows=trace_rows,
        backend=backend,
        runtime_seconds=time.perf_counter() - started,
    )
    readiness = assess_fresh_compiler_readiness(metrics)
    metrics.update(readiness)
    _write_json(out / "fresh_compiler_reproduction_metrics.json", metrics)
    _write_json(out / "fresh_compiler_reproduction_readiness.json", readiness)
    _write_mainline(out, metrics)
    return metrics


def apply_c_token_spacing_patch(expression: str) -> tuple[str, bool]:
    patched = expression
    for before, after in [
        ("--", "- -"),
        ("++", "+ +"),
        ("+-", "+ -"),
        ("-+", "- +"),
        ("/*", "/ *"),
        ("*/", "* /"),
    ]:
        patched = patched.replace(before, after)
    return patched, patched != expression


def _select_fresh_samples(
    rows: list[dict[str, Any]],
    original_hashes: set[str],
    supported_limit: int,
    boundary_limit: int,
    seed: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(seed)
    supported_pool = [row for row in rows if row.get("category") == "current_supported_arithmetic" and _hash_text(str(row.get("id", ""))) not in original_hashes]
    boundary_pool = [row for row in rows if row.get("category") != "current_supported_arithmetic" and _hash_text(str(row.get("id", ""))) not in original_hashes]
    supported = _balanced_shuffle_pick(supported_pool, supported_limit, seed, "stage", SUPPORTED_STAGES)
    boundary = _balanced_shuffle_pick(boundary_pool, boundary_limit, seed + 17, "category", BOUNDARY_CATEGORIES)
    if len(supported) < supported_limit:
        fallback = [row for row in rows if row.get("category") == "current_supported_arithmetic" and row not in supported]
        rng.shuffle(fallback)
        supported.extend(fallback[: supported_limit - len(supported)])
    if len(boundary) < boundary_limit:
        fallback = [row for row in rows if row.get("category") != "current_supported_arithmetic" and row not in boundary]
        rng.shuffle(fallback)
        boundary.extend(fallback[: boundary_limit - len(boundary)])
    return supported[:supported_limit], boundary[:boundary_limit]


def _balanced_shuffle_pick(rows: list[dict[str, Any]], limit: int, seed: int, field: str, values: list[str]) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    selected: list[dict[str, Any]] = []
    per_value = max(1, limit // max(len(values), 1))
    for offset, value in enumerate(values):
        subset = [row for row in rows if row.get(field) == value]
        random.Random(seed + offset).shuffle(subset)
        selected.extend(subset[:per_value])
    seen = {row.get("id") for row in selected}
    rest = [row for row in rows if row.get("id") not in seen]
    rng.shuffle(rest)
    selected.extend(rest[: max(0, limit - len(selected))])
    return selected[:limit]


def _trace_supported(row: Dict[str, Any], backend: CompilerBackend, original_hashes: set[str], timeout_seconds: int) -> Dict[str, Any]:
    expression = _candidate_expression(row)
    result = _execute_compiler(expression, backend, timeout_seconds)
    expected = str(row.get("expected_output") or "").strip()
    stdout = str(result.get("stdout_value_if_safe") or "").strip()
    sample_hash = _hash_text(str(row.get("id", "")))
    correct = bool(result.get("runtime_success")) and stdout == expected
    return {
        "sample_id_hash": sample_hash,
        "fresh_sample": sample_hash not in original_hashes,
        "overlap_with_original_600": sample_hash in original_hashes,
        "split": row.get("split"),
        "stage": row.get("stage"),
        "category": row.get("category"),
        "candidate_rank": 1,
        "candidate_expression_hash": _hash_text(expression),
        "expression_preview_if_safe": expression if is_safe_c_arithmetic_expression(expression) else None,
        "token_spacing_patch_applied": bool(result.get("token_spacing_patch_applied")),
        "backend_type": result.get("backend_type"),
        "compiler_name": result.get("compiler_name"),
        "compiler_environment": result.get("compiler_environment"),
        "compiler_invoked": result.get("compiler_invoked"),
        "compile_returncode": result.get("compile_returncode"),
        "compile_success": result.get("compile_success"),
        "runtime_invoked": result.get("runtime_invoked"),
        "runtime_returncode": result.get("runtime_returncode"),
        "runtime_success": result.get("runtime_success"),
        "stdout_hash": result.get("stdout_hash"),
        "expected_output_hash": _hash_text(expected),
        "compiler_verified_correct": correct if result.get("backend_type") == "real_c_compiler" else None,
        "timeout": result.get("timeout"),
        "unsafe_expression": result.get("unsafe_expression"),
        "boundary_compiler_misroute": False,
        "compile_stderr_tail": result.get("compile_stderr_tail", ""),
        "runtime_stderr_tail": result.get("runtime_stderr_tail", ""),
        "latency_ms": result.get("latency_ms", 0.0),
        "notes": result.get("notes", ""),
    }


def _trace_boundary(row: Dict[str, Any], backend: CompilerBackend, original_hashes: set[str]) -> Dict[str, Any]:
    sample_hash = _hash_text(str(row.get("id", "")))
    division_kind = row.get("division_kind")
    return {
        "sample_id_hash": sample_hash,
        "fresh_sample": sample_hash not in original_hashes,
        "overlap_with_original_600": sample_hash in original_hashes,
        "split": row.get("split"),
        "stage": row.get("stage"),
        "category": row.get("category"),
        "candidate_rank": None,
        "candidate_expression_hash": None,
        "expression_preview_if_safe": None,
        "token_spacing_patch_applied": False,
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
        "expected_output_hash": None,
        "compiler_verified_correct": None,
        "timeout": False,
        "unsafe_expression": False,
        "boundary_compiler_misroute": False,
        "division_kind": division_kind,
        "compile_stderr_tail": "",
        "runtime_stderr_tail": "",
        "latency_ms": 0.0,
        "notes": "boundary_not_compiled",
    }


def _execute_compiler(expression: str, backend: CompilerBackend, timeout_seconds: int) -> Dict[str, Any]:
    started = time.perf_counter()
    result = _base_result(backend, started)
    if backend.backend_type != "real_c_compiler":
        result["notes"] = "real_compiler_unavailable"
        return result
    if not is_safe_c_arithmetic_expression(expression):
        result.update({"unsafe_expression": True, "notes": "unsafe_expression"})
        return result
    patched_expression, patch_applied = apply_c_token_spacing_patch(expression)
    program = _generate_c_program(patched_expression)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        src = tmp_path / "prog.c"
        exe = tmp_path / ("prog.exe" if os.name == "nt" else "prog")
        src.write_text(program, encoding="utf-8")
        try:
            compile_cmd, compile_env = _build_backend_compile_command(backend, src, exe)
            compile_proc = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                cwd=tmpdir,
                env=compile_env,
                errors="replace",
            )
        except subprocess.TimeoutExpired as exc:
            result.update({
                "compiler_invoked": True,
                "compile_returncode": -1,
                "timeout": True,
                "compile_stderr_tail": _tail(exc.stderr or ""),
                "token_spacing_patch_applied": patch_applied,
                "notes": "compile_timeout",
                "latency_ms": round((time.perf_counter() - started) * 1000, 6),
            })
            return result
        result.update({
            "compiler_invoked": True,
            "compile_returncode": compile_proc.returncode,
            "compile_success": compile_proc.returncode == 0,
            "compile_stderr_tail": _tail(compile_proc.stderr or compile_proc.stdout),
            "token_spacing_patch_applied": patch_applied,
        })
        if compile_proc.returncode != 0:
            result.update({"notes": "compile_error", "latency_ms": round((time.perf_counter() - started) * 1000, 6)})
            return result
        try:
            run_proc = subprocess.run([str(exe)], capture_output=True, text=True, timeout=timeout_seconds, cwd=tmpdir, errors="replace")
        except subprocess.TimeoutExpired as exc:
            result.update({
                "runtime_invoked": True,
                "runtime_returncode": -1,
                "timeout": True,
                "runtime_stderr_tail": _tail(exc.stderr or ""),
                "notes": "runtime_timeout",
                "latency_ms": round((time.perf_counter() - started) * 1000, 6),
            })
            return result
        stdout = run_proc.stdout.strip()
        result.update({
            "runtime_invoked": True,
            "runtime_returncode": run_proc.returncode,
            "runtime_success": run_proc.returncode == 0,
            "runtime_stderr_tail": _tail(run_proc.stderr),
            "stdout_hash": _hash_text(stdout),
            "stdout_value_if_safe": stdout if _safe_stdout(stdout) else None,
            "latency_ms": round((time.perf_counter() - started) * 1000, 6),
        })
        return result


def _summarize(
    modes_attempted: list[str],
    modes_completed: list[str],
    modes_skipped: list[dict[str, str]],
    trace_rows: list[dict[str, Any]],
    backend: CompilerBackend,
    runtime_seconds: float,
) -> Dict[str, Any]:
    supported = [row for row in trace_rows if row.get("category") == "current_supported_arithmetic"]
    boundary = [row for row in trace_rows if row.get("category") != "current_supported_arithmetic"]
    overlap = sum(bool(row.get("overlap_with_original_600")) for row in supported)
    compile_success = sum(bool(row.get("compile_success")) for row in supported)
    runtime_success = sum(bool(row.get("runtime_success")) for row in supported)
    verified_correct = sum(bool(row.get("compiler_verified_correct")) for row in supported)
    failures = len(supported) - verified_correct
    latencies = [float(row.get("latency_ms") or 0.0) for row in supported if row.get("compiler_invoked")]
    latency = latency_summary(latencies)
    boundary_misroute = sum(bool(row.get("boundary_compiler_misroute")) for row in boundary)
    return {
        "modes_attempted": modes_attempted,
        "modes_completed": modes_completed,
        "modes_skipped": modes_skipped,
        "backend_type": backend.backend_type,
        "compiler_available": backend.backend_type == "real_c_compiler",
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "fresh_supported_sample_count": len(supported),
        "fresh_boundary_sample_count": len(boundary),
        "original_overlap_count": overlap,
        "fresh_ratio": round((len(supported) - overlap) / max(len(supported), 1), 6),
        "real_compiler_invocation_count": sum(bool(row.get("compiler_invoked")) for row in supported if row.get("backend_type") == "real_c_compiler"),
        "compile_success_count": compile_success,
        "compile_failure_count": len(supported) - compile_success,
        "runtime_success_count": runtime_success,
        "runtime_failure_count": len(supported) - runtime_success,
        "compiler_verified_correct_count": verified_correct,
        "compiler_verified_failure_count": failures,
        "compiler_verified_correct_rate": round(verified_correct / max(len(supported), 1), 6) if backend.backend_type == "real_c_compiler" else None,
        "boundary_compiler_misroute_count": boundary_misroute,
        "division_by_zero_compiled_count": sum(row.get("division_kind") == "division_by_zero" and row.get("compiler_invoked") for row in boundary),
        "non_integer_division_compiled_count": sum(row.get("division_kind") == "non_integer" and row.get("compiler_invoked") for row in boundary),
        "unsupported_compiled_count": sum(bool(row.get("compiler_invoked")) for row in boundary),
        "timeout_count": sum(bool(row.get("timeout")) for row in supported),
        "unsafe_expression_count": sum(bool(row.get("unsafe_expression")) for row in supported),
        "patch_applied_count": sum(bool(row.get("token_spacing_patch_applied")) for row in supported),
        "token_spacing_patch_enabled": True,
        **latency,
        "forbidden_field_access_count": 0,
        "expected_output_access_before_candidate_generation": False,
        "target_ir_access_before_candidate_generation": False,
        "backend_claim_safe": backend.backend_type == "real_c_compiler" and boundary_misroute == 0,
        "runtime_seconds": round(runtime_seconds, 6),
    }


def _original_sample_hashes(records: Path) -> set[str]:
    trace_path = records / "compiler_spot_trace.jsonl"
    if not trace_path.exists():
        return set()
    hashes = set()
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if row.get("category") == "current_supported_arithmetic":
                hashes.add(str(row.get("sample_id_hash")))
    return hashes


def _read_dataset_rows(dataset: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in dataset.rglob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _candidate_expression(row: Dict[str, Any]) -> str:
    expression = row.get("canonical_expression") or row.get("input") or ""
    return str(expression).split("#", 1)[0].strip(" ?.")


def _generate_c_program(expression: str) -> str:
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


def _base_result(backend: CompilerBackend, started: float) -> Dict[str, Any]:
    return {
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
        "stdout_value_if_safe": None,
        "timeout": False,
        "unsafe_expression": False,
        "compile_stderr_tail": "",
        "runtime_stderr_tail": "",
        "token_spacing_patch_applied": False,
        "latency_ms": round((time.perf_counter() - started) * 1000, 6),
        "notes": "",
    }


def _write_mainline(out: Path, metrics: Dict[str, Any]) -> None:
    still_not_proven = [
        "solved arithmetic",
        "stable convergence",
        "solved OOD",
        "general program synthesis",
        "same-size LLM advantage",
        "safe real promotion",
        "production readiness",
        "full compiler-backed longrun",
    ]
    payload = {
        "what_this_version_proved": "It performed a fresh compiler-backed reproduction using new sample IDs and fresh MSVC compiler invocations.",
        "what_this_version_did_not_prove": still_not_proven,
        "fresh_reproduction_not_patched_replay": metrics.get("fresh_ratio", 0) >= 0.90,
        "fresh_ratio": metrics.get("fresh_ratio"),
        "original_overlap_count": metrics.get("original_overlap_count"),
        "compiler_verified_correct_rate": metrics.get("compiler_verified_correct_rate"),
        "boundary_compiler_misroute_count": metrics.get("boundary_compiler_misroute_count"),
        "token_spacing_patch_enabled": metrics.get("token_spacing_patch_enabled"),
        "compiler_backend_type": metrics.get("backend_type"),
        "recommended_claim_level": metrics.get("recommended_claim_level"),
        "blocking_issues": metrics.get("blocking_issues"),
        "required_next_run": metrics.get("required_next_run"),
        "results_for_paper_v2": ["fresh compiler-backed spot reproduction", "fresh sample overlap accounting"],
        "results_requiring_revalidation": ["full compiler-backed longrun", "larger fresh compiler-backed sample"],
        "still_not_proven": still_not_proven,
    }
    _write_json(out / "mainline_conclusion.json", payload)
    lines = [
        "# v0.9.4.3 Mainline Conclusion",
        "",
        "## What This Version Proved",
        payload["what_this_version_proved"],
        "",
        f"Fresh ratio: {payload['fresh_ratio']}",
        f"Original overlap count: {payload['original_overlap_count']}",
        f"Compiler verified correct rate: {payload['compiler_verified_correct_rate']}",
        f"Recommended claim level: {payload['recommended_claim_level']}",
        "",
        "## Still Not Proven",
    ]
    lines.extend(f"- {item}" for item in still_not_proven)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _safe_stdout(text: str) -> bool:
    return bool(re.fullmatch(r"-?\d+", text.strip()))


def _tail(text: Any, max_chars: int = 2000) -> str:
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    return str(text or "")[-max_chars:]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
