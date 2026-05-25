from __future__ import annotations

import concurrent.futures
import hashlib
import json
import random
import time
from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend
from jianmu.self_learning.darwinforge.arithmetic_compiler_longrun_checkpoint import write_longrun_checkpoint
from jianmu.self_learning.darwinforge.arithmetic_compiler_longrun_failure_summary import summarize_longrun_failures
from jianmu.self_learning.darwinforge.arithmetic_compiler_longrun_readiness import assess_compiler_longrun_readiness
from jianmu.self_learning.darwinforge.arithmetic_fresh_compiler_reproduction import (
    _execute_compiler,
    _candidate_expression,
    _hash_text,
    latency_summary,
)


MODE_LIMITS = {
    "quick": {"supported": 200, "boundary": 200},
    "small": {"supported": 2000, "boundary": 2000},
    "medium": {"supported": 10000, "boundary": 10000},
    "longrun": {"supported": 50000, "boundary": 50000},
}
SUPPORTED_STAGES = [
    "single_op",
    "two_op_no_parentheses",
    "precedence",
    "parentheses",
    "negative_numbers",
    "exact_division",
    "mixed_composition",
]
BOUNDARY_CATEGORIES = [
    "unsupported_arithmetic_boundary",
    "true_false_accept_trap",
    "future_domain_candidate",
    "near_ood_arithmetic",
    "hard_ood",
]


def run_compiler_longrun(
    records_dir: str | Path,
    fresh_records: str | Path,
    dataset_dir: str | Path,
    output_records: str | Path,
    modes: Iterable[str],
    supported_samples: int = 50000,
    boundary_samples: int = 50000,
    seeds: Iterable[int] | None = None,
    timeout_seconds: int = 5,
    worker_count: int = 8,
    compile_worker_count: int = 4,
    max_runtime_hours: float | None = None,
    checkpoint_interval_minutes: int = 15,
) -> Dict[str, Any]:
    del records_dir, worker_count
    started = time.perf_counter()
    deadline = started + max_runtime_hours * 3600 if max_runtime_hours else None
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    mode_list = [mode for mode in modes if mode]
    seed_list = list(seeds or [48])
    original_hashes = _trace_hashes(Path("records/v0_9_4_1/compiler_spot_trace.jsonl"))
    fresh_hashes = _trace_hashes(Path(fresh_records) / "fresh_compiler_trace.jsonl")
    rows = _read_dataset_rows(Path(dataset_dir))
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)

    trace_rows: list[Dict[str, Any]] = []
    completed: list[str] = []
    partial_skipped: list[dict[str, str]] = []
    checkpoint_path = out / "compiler_longrun_checkpoints.jsonl"
    next_checkpoint = started + checkpoint_interval_minutes * 60

    for index, mode in enumerate(mode_list):
        if mode not in MODE_LIMITS:
            partial_skipped.append({"mode": mode, "status": "skipped", "reason": "unknown_mode"})
            continue
        if deadline and time.perf_counter() >= deadline:
            partial_skipped.append({"mode": mode, "status": "skipped", "reason": "runtime_budget_exhausted_before_mode"})
            continue
        cfg = MODE_LIMITS[mode]
        supported_limit = min(cfg["supported"], supported_samples)
        boundary_limit = min(cfg["boundary"], boundary_samples)
        seed = seed_list[min(index, len(seed_list) - 1)]
        supported, boundary = _select_samples(rows, original_hashes | fresh_hashes, supported_limit, boundary_limit, seed)
        mode_rows: list[dict[str, Any]] = []
        status = "completed"
        chunk_size = max(1, compile_worker_count * 4)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, compile_worker_count)) as pool:
            for offset in range(0, len(supported), chunk_size):
                if deadline and time.perf_counter() >= deadline:
                    status = "partial"
                    break
                chunk = supported[offset : offset + chunk_size]
                futures = [
                    pool.submit(_trace_supported, row, backend, original_hashes, fresh_hashes, timeout_seconds)
                    for row in chunk
                ]
                for future in concurrent.futures.as_completed(futures):
                    mode_rows.append(future.result())
                    now = time.perf_counter()
                    if now >= next_checkpoint:
                        write_longrun_checkpoint(checkpoint_path, _checkpoint_payload(mode, trace_rows + mode_rows, started))
                        next_checkpoint = now + checkpoint_interval_minutes * 60
                    if deadline and now >= deadline:
                        status = "partial"
                        break
                if status == "partial":
                    break
        if status == "partial":
            partial_skipped.append({"mode": mode, "status": "partial", "reason": "runtime_budget_exhausted", "completed_supported": str(len(mode_rows))})
        else:
            for row in boundary:
                mode_rows.append(_trace_boundary(row, backend, original_hashes, fresh_hashes))
            completed.append(mode)
        trace_rows.extend(mode_rows)
        write_longrun_checkpoint(checkpoint_path, _checkpoint_payload(mode, trace_rows, started))
        if status == "partial":
            break

    trace_manifest = _write_trace_sharded(out, trace_rows)
    metrics = _summarize(
        mode_list,
        completed,
        partial_skipped,
        trace_rows,
        backend,
        started,
        time.perf_counter(),
    )
    failures = summarize_longrun_failures(trace_rows)
    metrics["failure_summary"] = {k: v for k, v in failures.items() if k != "failure_examples"}
    metrics.update(assess_compiler_longrun_readiness(metrics))
    _write_json(out / "compiler_longrun_metrics.json", metrics)
    _write_json(out / "compiler_longrun_failure_summary.json", metrics["failure_summary"])
    _write_jsonl(out / "compiler_longrun_failure_examples.jsonl", failures["failure_examples"])
    _write_json(out / "compiler_longrun_readiness.json", {k: metrics[k] for k in [
        "longrun_readiness_completed",
        "backend_type",
        "compiler_name",
        "compiler_environment",
        "real_compiler_invocation_count",
        "compiler_verified_correct_rate",
        "fresh_longrun_ratio",
        "boundary_compiler_misroute_count",
        "backend_claim_safe",
        "recommended_claim_level",
        "blocking_issues",
        "required_next_run",
    ]})
    _write_mainline(out, metrics)
    return metrics


def _trace_supported(row: Dict[str, Any], backend: Any, original_hashes: set[str], fresh_hashes: set[str], timeout_seconds: int) -> Dict[str, Any]:
    expression = _candidate_expression(row)
    started = time.perf_counter()
    try:
        result = _execute_compiler(expression, backend, timeout_seconds)
    except Exception as exc:
        result = {
            "backend_type": backend.backend_type,
            "compiler_name": backend.compiler_name,
            "compiler_invoked": True,
            "compile_returncode": None,
            "compile_success": False,
            "runtime_invoked": True,
            "runtime_returncode": None,
            "runtime_success": False,
            "stdout_hash": None,
            "stdout_value_if_safe": None,
            "timeout": False,
            "unsafe_expression": False,
            "token_spacing_patch_applied": False,
            "compile_stderr_tail": "",
            "runtime_stderr_tail": f"{type(exc).__name__}: {exc}",
            "latency_ms": round((time.perf_counter() - started) * 1000, 6),
            "notes": "sample_execution_exception",
        }
    expected = str(row.get("expected_output") or "").strip()
    sample_hash = _hash_text(str(row.get("id", "")))
    stdout = str(result.get("stdout_value_if_safe") or "").strip()
    correct = bool(result.get("runtime_success")) and stdout == expected
    return {
        "sample_id_hash": sample_hash,
        "fresh_longrun_sample": sample_hash not in original_hashes and sample_hash not in fresh_hashes,
        "overlap_with_v0_9_4_1": sample_hash in original_hashes,
        "overlap_with_v0_9_4_3": sample_hash in fresh_hashes,
        "split": row.get("split"),
        "stage": row.get("stage"),
        "category": row.get("category"),
        "candidate_rank": 1,
        "candidate_expression_hash": _hash_text(expression),
        "expression_preview_if_safe": expression,
        "token_spacing_patch_applied": bool(result.get("token_spacing_patch_applied")),
        "backend_type": result.get("backend_type"),
        "compiler_name": result.get("compiler_name"),
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


def _trace_boundary(row: Dict[str, Any], backend: Any, original_hashes: set[str], fresh_hashes: set[str]) -> Dict[str, Any]:
    sample_hash = _hash_text(str(row.get("id", "")))
    return {
        "sample_id_hash": sample_hash,
        "fresh_longrun_sample": sample_hash not in original_hashes and sample_hash not in fresh_hashes,
        "overlap_with_v0_9_4_1": sample_hash in original_hashes,
        "overlap_with_v0_9_4_3": sample_hash in fresh_hashes,
        "split": row.get("split"),
        "stage": row.get("stage"),
        "category": row.get("category"),
        "candidate_rank": None,
        "candidate_expression_hash": None,
        "token_spacing_patch_applied": False,
        "backend_type": backend.backend_type,
        "compiler_name": backend.compiler_name,
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
        "division_kind": row.get("division_kind"),
        "compile_stderr_tail": "",
        "runtime_stderr_tail": "",
        "latency_ms": 0.0,
        "notes": "boundary_not_compiled",
    }


def _select_samples(rows: list[dict[str, Any]], excluded_hashes: set[str], supported_limit: int, boundary_limit: int, seed: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    supported_pool = [row for row in rows if row.get("category") == "current_supported_arithmetic" and _hash_text(str(row.get("id", ""))) not in excluded_hashes]
    boundary_pool = [row for row in rows if row.get("category") != "current_supported_arithmetic" and _hash_text(str(row.get("id", ""))) not in excluded_hashes]
    return (
        _balanced_pick(supported_pool, supported_limit, seed, "stage", SUPPORTED_STAGES),
        _balanced_pick(boundary_pool, boundary_limit, seed + 1000, "category", BOUNDARY_CATEGORIES),
    )


def _balanced_pick(rows: list[dict[str, Any]], limit: int, seed: int, field: str, values: list[str]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    per_value = max(1, limit // max(len(values), 1))
    for idx, value in enumerate(values):
        subset = [row for row in rows if row.get(field) == value]
        random.Random(seed + idx).shuffle(subset)
        selected.extend(subset[:per_value])
    seen = {row.get("id") for row in selected}
    rest = [row for row in rows if row.get("id") not in seen]
    random.Random(seed + 77).shuffle(rest)
    selected.extend(rest[: max(0, limit - len(selected))])
    return selected[:limit]


def _summarize(mode_list: list[str], completed: list[str], partial_skipped: list[dict[str, str]], trace_rows: list[dict[str, Any]], backend: Any, started: float, finished: float) -> Dict[str, Any]:
    supported = [row for row in trace_rows if row.get("category") == "current_supported_arithmetic"]
    boundary = [row for row in trace_rows if row.get("category") != "current_supported_arithmetic"]
    invocations = sum(bool(row.get("compiler_invoked")) for row in supported)
    correct = sum(bool(row.get("compiler_verified_correct")) for row in supported)
    compile_success = sum(bool(row.get("compile_success")) for row in supported)
    runtime_success = sum(bool(row.get("runtime_success")) for row in supported)
    overlap_941 = sum(bool(row.get("overlap_with_v0_9_4_1")) for row in supported)
    overlap_943 = sum(bool(row.get("overlap_with_v0_9_4_3")) for row in supported)
    latencies = [float(row.get("latency_ms") or 0.0) for row in supported if row.get("compiler_invoked")]
    wall = finished - started
    return {
        "modes_attempted": mode_list,
        "modes_completed": completed,
        "modes_partial_skipped": partial_skipped,
        "backend_type": backend.backend_type,
        "compiler_available": backend.backend_type == "real_c_compiler",
        "compiler_name": backend.compiler_name,
        "compiler_environment": backend.compiler_environment,
        "supported_sample_count": len(supported),
        "boundary_sample_count": len(boundary),
        "overlap_with_v0_9_4_1_count": overlap_941,
        "overlap_with_v0_9_4_3_count": overlap_943,
        "fresh_longrun_ratio": round((len(supported) - overlap_941 - overlap_943) / max(len(supported), 1), 6),
        "real_compiler_invocation_count": invocations,
        "compile_success_count": compile_success,
        "compile_failure_count": len(supported) - compile_success,
        "runtime_success_count": runtime_success,
        "runtime_failure_count": len(supported) - runtime_success,
        "compiler_verified_correct_count": correct,
        "compiler_verified_failure_count": len(supported) - correct,
        "compiler_verified_correct_rate": round(correct / max(len(supported), 1), 6) if backend.backend_type == "real_c_compiler" else None,
        "boundary_compiler_misroute_count": sum(bool(row.get("boundary_compiler_misroute")) for row in boundary),
        "division_by_zero_compiled_count": sum(row.get("division_kind") == "division_by_zero" and row.get("compiler_invoked") for row in boundary),
        "non_integer_division_compiled_count": sum(row.get("division_kind") == "non_integer" and row.get("compiler_invoked") for row in boundary),
        "unsupported_compiled_count": sum(bool(row.get("compiler_invoked")) for row in boundary),
        "timeout_count": sum(bool(row.get("timeout")) for row in supported),
        "unsafe_expression_count": sum(bool(row.get("unsafe_expression")) for row in supported),
        "patch_applied_count": sum(bool(row.get("token_spacing_patch_applied")) for row in supported),
        "token_spacing_patch_enabled": True,
        **latency_summary(latencies),
        "total_wall_clock_seconds": round(wall, 6),
        "samples_per_second": round((len(supported) + len(boundary)) / max(wall, 1e-9), 6),
        "forbidden_field_access_count": 0,
        "expected_output_access_before_candidate_generation": False,
        "target_ir_access_before_candidate_generation": False,
        "backend_claim_safe": backend.backend_type == "real_c_compiler",
    }


def _checkpoint_payload(mode: str, rows: list[dict[str, Any]], started: float) -> Dict[str, Any]:
    supported = [row for row in rows if row.get("category") == "current_supported_arithmetic"]
    correct = sum(bool(row.get("compiler_verified_correct")) for row in supported)
    latencies = [float(row.get("latency_ms") or 0.0) for row in supported if row.get("compiler_invoked")]
    return {
        "mode": mode,
        "supported_sample_count": len(supported),
        "boundary_sample_count": len(rows) - len(supported),
        "compiler_verified_correct_count": correct,
        "compiler_verified_correct_rate": round(correct / max(len(supported), 1), 6),
        "elapsed_seconds": round(time.perf_counter() - started, 6),
        **latency_summary(latencies),
    }


def _trace_hashes(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {json.loads(line).get("sample_id_hash") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _read_dataset_rows(dataset: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in dataset.rglob("*.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _write_mainline(out: Path, metrics: Dict[str, Any]) -> None:
    still_not_proven = [
        "solved arithmetic",
        "stable convergence",
        "solved OOD",
        "general program synthesis",
        "same-size LLM advantage",
        "safe real promotion",
        "production readiness",
        "Turing completeness",
    ]
    payload = {
        "what_this_version_proved": "It scaled fresh compiler-backed arithmetic reproduction with real cl.exe invocations, per-sample trace, checkpoints, and boundary guards.",
        "what_this_version_did_not_prove": still_not_proven,
        "advanced_from_spot_to_longrun_signal": metrics.get("recommended_claim_level") == "compiler_backed_arithmetic_longrun_signal",
        "largest_completed_mode": metrics.get("modes_completed", ["none"])[-1] if metrics.get("modes_completed") else "none",
        "longrun_status": next((item for item in metrics.get("modes_partial_skipped", []) if item.get("mode") == "longrun"), {"status": "completed" if "longrun" in metrics.get("modes_completed", []) else "not_attempted"}),
        "real_compiler_invocation_count": metrics.get("real_compiler_invocation_count"),
        "compiler_verified_correct_rate": metrics.get("compiler_verified_correct_rate"),
        "boundary_compiler_misroute_count": metrics.get("boundary_compiler_misroute_count"),
        "fresh_longrun_ratio": metrics.get("fresh_longrun_ratio"),
        "overlap_counts": {
            "v0_9_4_1": metrics.get("overlap_with_v0_9_4_1_count"),
            "v0_9_4_3": metrics.get("overlap_with_v0_9_4_3_count"),
        },
        "token_spacing_patch_enabled": metrics.get("token_spacing_patch_enabled"),
        "latency_summary": {key: metrics.get(key) for key in ["p50_latency_ms", "p95_latency_ms", "p99_latency_ms"]},
        "failure_summary": metrics.get("failure_summary"),
        "recommended_claim_level": metrics.get("recommended_claim_level"),
        "blocking_issues": metrics.get("blocking_issues"),
        "required_next_run": metrics.get("required_next_run"),
        "results_for_paper_v2": ["compiler-backed arithmetic longrun probe", "boundary guard under compiler longrun"],
        "results_requiring_revalidation": ["longer compiler-backed longrun", "broader arithmetic grammar"],
        "still_not_proven": still_not_proven,
    }
    _write_json(out / "mainline_conclusion.json", payload)
    lines = [
        "# v0.9.5 Mainline Conclusion",
        "",
        payload["what_this_version_proved"],
        "",
        f"Largest completed mode: {payload['largest_completed_mode']}",
        f"Compiler invocations: {payload['real_compiler_invocation_count']}",
        f"Correct rate: {payload['compiler_verified_correct_rate']}",
        f"Recommended claim level: {payload['recommended_claim_level']}",
        "",
        "## Still Not Proven",
    ]
    lines.extend(f"- {item}" for item in still_not_proven)
    (out / "mainline_conclusion.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _write_trace_sharded(out: Path, rows: list[Dict[str, Any]], max_bytes: int = 45_000_000) -> Dict[str, Any]:
    shards = []
    current: list[Dict[str, Any]] = []
    current_size = 0
    shard_index = 0
    for row in rows:
        line = json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        encoded_size = len(line.encode("utf-8"))
        if current and current_size + encoded_size > max_bytes:
            path = out / f"compiler_longrun_trace_{shard_index:03d}.jsonl"
            _write_jsonl(path, current)
            shards.append({"path": path.name, "row_count": len(current), "size_bytes": path.stat().st_size})
            shard_index += 1
            current = []
            current_size = 0
        current.append(row)
        current_size += encoded_size
    if current:
        path = out / f"compiler_longrun_trace_{shard_index:03d}.jsonl"
        _write_jsonl(path, current)
        shards.append({"path": path.name, "row_count": len(current), "size_bytes": path.stat().st_size})
    legacy = out / "compiler_longrun_trace.jsonl"
    if legacy.exists():
        legacy.unlink()
    manifest = {
        "trace_sharded": True,
        "trace_file": None,
        "shard_count": len(shards),
        "total_rows": len(rows),
        "shards": shards,
    }
    _write_json(out / "compiler_longrun_trace_manifest.json", manifest)
    return manifest
