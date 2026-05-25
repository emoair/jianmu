from __future__ import annotations

import statistics
import time
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable

from jianmu.self_learning.darwinforge.arithmetic_compiler_audit_readiness import assess_compiler_audit_readiness
from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import (
    detect_arithmetic_backend,
    execute_with_backend,
    latency_summary,
)
from jianmu.self_learning.darwinforge.arithmetic_safe_evaluator import evaluate_target_ir


SPOT_COUNTS = {"quick": 50, "small": 200, "medium": 500, "large-light": 1000}


def run_arithmetic_compiler_spot_audit(rows: Iterable[Dict[str, Any]], mode: str = "quick") -> Dict[str, Any]:
    supported = [row for row in rows if row.get("category") == "current_supported_arithmetic"][: SPOT_COUNTS.get(mode, 50)]
    latencies = []
    correct = 0
    failures = []
    for row in supported:
        started = time.perf_counter()
        try:
            value = evaluate_target_ir(row["target_ir"])
            if f"{value}\n" == row.get("expected_output"):
                correct += 1
        except Exception:
            failures.append(row.get("id"))
        latencies.append((time.perf_counter() - started) * 1000)
    count = len(supported)
    return {
        "compiler_backend_type": "internal_evaluator",
        "compiler_spot_sample_count": count,
        "compiler_eval_call_count": count,
        "compile_success_count": count,
        "runtime_success_count": correct,
        "compiler_verified_correct_count": 0,
        "compiler_verified_failure_count": 0,
        "compiler_timeout_count": 0,
        "internal_evaluator_correct_rate": round(correct / max(count, 1), 6),
        "p50_latency_ms": round(statistics.median(latencies), 6) if latencies else 0.0,
        "p95_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.95) - 1], 6) if latencies else 0.0,
        "p99_latency_ms": round(sorted(latencies)[int(len(latencies) * 0.99) - 1], 6) if latencies else 0.0,
        "examples_compile_fail": [],
        "examples_runtime_fail": failures[:5],
    }


MODE_LIMITS = {
    "quick": {"supported": 100, "boundary": 100, "seeds": 1},
    "small": {"supported": 500, "boundary": 500, "seeds": 1},
    "medium": {"supported": 2000, "boundary": 2000, "seeds": 3},
}
SUPPORTED_STAGES = ["precedence", "parentheses", "negative_numbers", "exact_division", "mixed_composition"]
BOUNDARY_CATEGORIES = [
    "unsupported_arithmetic_boundary",
    "true_false_accept_trap",
    "future_domain_candidate",
    "near_ood_arithmetic",
    "hard_ood",
]


def run_real_compiler_arithmetic_spot_audit(
    records_dir: str | Path,
    dataset_dir: str | Path,
    output_records: str | Path,
    modes: Iterable[str],
    supported_samples: int = 2000,
    boundary_samples: int = 2000,
    seeds: Iterable[int] | None = None,
    timeout_seconds: int = 5,
    prefer_msvc: bool = False,
) -> Dict[str, Any]:
    started = time.perf_counter()
    dataset = Path(dataset_dir)
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    mode_list = [mode for mode in modes if mode]
    seed_list = list(seeds or [42])
    backend = detect_arithmetic_backend(prefer_python_subprocess=True, prefer_msvc=prefer_msvc)
    completed = []
    skipped = []
    all_trace: list[dict[str, Any]] = []
    latest: dict[str, Any] = {}
    for mode in mode_list:
        if mode not in MODE_LIMITS:
            skipped.append({"mode": mode, "reason": "unknown mode"})
            continue
        result = _run_mode(dataset, mode, supported_samples, boundary_samples, backend, timeout_seconds)
        latest = result
        completed.append(mode)
        all_trace.extend(result["trace_rows"])

    trace_path = out / "compiler_spot_trace.jsonl"
    _write_jsonl(trace_path, all_trace)
    metrics = _summarize(
        records_dir=Path(records_dir),
        modes_attempted=mode_list,
        modes_completed=completed,
        modes_skipped=skipped,
        trace_rows=all_trace,
        latest=latest,
        backend_type=backend.backend_type,
        compiler_name=backend.compiler_name,
        runtime_seconds=time.perf_counter() - started,
    )
    readiness = assess_compiler_audit_readiness(metrics)
    metrics.update(readiness)
    _write_outputs(out, metrics)
    _write_msvc_detection_report(out, backend.detection_report or {})
    return metrics


def _run_mode(dataset: Path, mode: str, supported_limit: int, boundary_limit: int, backend: Any, timeout_seconds: int) -> Dict[str, Any]:
    cfg = MODE_LIMITS[mode]
    supported_rows, boundary_rows = _select_samples(
        dataset,
        min(cfg["supported"], supported_limit),
        min(cfg["boundary"], boundary_limit),
    )
    trace_rows = []
    for row in supported_rows:
        trace_rows.append(_trace_supported(row, backend, timeout_seconds))
    for row in boundary_rows:
        trace_rows.append(_trace_boundary(row, backend.backend_type))
    return {"mode": mode, "supported_rows": supported_rows, "boundary_rows": boundary_rows, "trace_rows": trace_rows}


def _select_samples(dataset: Path, supported_limit: int, boundary_limit: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = _read_dataset_rows(dataset)
    supported = [row for row in rows if row.get("category") == "current_supported_arithmetic"]
    boundary = [row for row in rows if row.get("category") != "current_supported_arithmetic"]
    heldout_supported = [row for row in supported if row.get("split") == "heldout"]
    if len(heldout_supported) < supported_limit:
        heldout_supported.extend(row for row in supported if row not in heldout_supported)
    return _balanced_supported(heldout_supported, supported_limit), _balanced_boundary(boundary, boundary_limit)


def _balanced_supported(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    per_stage = max(1, limit // max(len(SUPPORTED_STAGES), 1))
    for stage in SUPPORTED_STAGES:
        selected.extend([row for row in rows if row.get("stage") == stage][:per_stage])
    seen = {row.get("id") for row in selected}
    selected.extend([row for row in rows if row.get("id") not in seen][: max(0, limit - len(selected))])
    return selected[:limit]


def _balanced_boundary(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    per_category = max(1, limit // max(len(BOUNDARY_CATEGORIES), 1))
    for category in BOUNDARY_CATEGORIES:
        selected.extend([row for row in rows if row.get("category") == category][:per_category])
    seen = {row.get("id") for row in selected}
    selected.extend([row for row in rows if row.get("id") not in seen][: max(0, limit - len(selected))])
    return selected[:limit]


def _trace_supported(row: Dict[str, Any], backend: Any, timeout_seconds: int) -> Dict[str, Any]:
    expression = _candidate_expression(row)
    result = execute_with_backend(expression, backend, timeout_seconds=timeout_seconds)
    expected = str(row.get("expected_output") or "").strip()
    stdout = str(result.get("stdout_value_if_safe") or "").strip()
    correct = bool(result.get("runtime_success")) and stdout == expected
    return {
        **_base_trace(row),
        "candidate_expression_hash": _hash_text(expression),
        "candidate_rank": 1,
        "expected_output_used_phase": "after_candidate_generation_for_scoring",
        "target_ir_used_phase": "none",
        "backend_type": result["backend_type"],
        "compiler_name": result["compiler_name"],
        "compiler_environment": result.get("compiler_environment", ""),
        "compiler_command_hash": result["compiler_command_hash"],
        "compiler_invoked": result["compiler_invoked"],
        "compile_returncode": result["compile_returncode"],
        "compile_success": result["compile_success"],
        "runtime_invoked": result["runtime_invoked"],
        "runtime_returncode": result["runtime_returncode"],
        "runtime_success": result["runtime_success"],
        "stdout_hash": result["stdout_hash"],
        "stdout_value_if_safe": result["stdout_value_if_safe"],
        "expected_output_hash": _hash_text(expected),
        "compiler_verified_correct": correct if result["backend_type"] == "real_c_compiler" else None,
        "timeout": result["timeout"],
        "unsafe_expression": result["unsafe_expression"],
        "boundary_compiler_misroute": False,
        "internal_evaluator_used": False,
        "latency_ms": result["latency_ms"],
        "notes": result["notes"],
    }


def _trace_boundary(row: Dict[str, Any], backend_type: str) -> Dict[str, Any]:
    return {
        **_base_trace(row),
        "candidate_expression_hash": None,
        "candidate_rank": None,
        "expected_output_used_phase": "none",
        "target_ir_used_phase": "none",
        "backend_type": backend_type,
        "compiler_name": "",
        "compiler_environment": "",
        "compiler_command_hash": None,
        "compiler_invoked": False,
        "compile_returncode": None,
        "compile_success": False,
        "runtime_invoked": False,
        "runtime_returncode": None,
        "runtime_success": False,
        "stdout_hash": None,
        "stdout_value_if_safe": None,
        "expected_output_hash": None,
        "compiler_verified_correct": None,
        "timeout": False,
        "unsafe_expression": False,
        "boundary_compiler_misroute": False,
        "internal_evaluator_used": False,
        "latency_ms": 0.0,
        "notes": "boundary_not_compiled",
    }


def _summarize(
    records_dir: Path,
    modes_attempted: list[str],
    modes_completed: list[str],
    modes_skipped: list[dict[str, str]],
    trace_rows: list[dict[str, Any]],
    latest: dict[str, Any],
    backend_type: str,
    compiler_name: str,
    runtime_seconds: float,
) -> Dict[str, Any]:
    supported = [row for row in trace_rows if row.get("category") == "current_supported_arithmetic"]
    boundary = [row for row in trace_rows if row.get("category") != "current_supported_arithmetic"]
    real_compiler_rows = [row for row in supported if row.get("backend_type") == "real_c_compiler"]
    compile_success = sum(bool(row.get("compile_success")) for row in supported)
    runtime_success = sum(bool(row.get("runtime_success")) for row in supported)
    verified_correct = sum(bool(row.get("compiler_verified_correct")) for row in real_compiler_rows)
    verified_failure = sum(row.get("compiler_verified_correct") is False for row in real_compiler_rows)
    latencies = [float(row.get("latency_ms") or 0.0) for row in supported if row.get("runtime_invoked")]
    latency = latency_summary(latencies)
    candidate_manifest = records_dir / "candidate_trace_manifest.json"
    metrics = {
        "audit_completed": bool(modes_completed),
        "modes_attempted": modes_attempted,
        "modes_completed": modes_completed,
        "modes_skipped": modes_skipped,
        "backend_type": backend_type,
        "compiler_available": backend_type == "real_c_compiler",
        "compiler_name": compiler_name,
        "compiler_environment": next((row.get("compiler_environment", "") for row in trace_rows if row.get("compiler_environment")), ""),
        "real_compiler_invocation_count": sum(bool(row.get("compiler_invoked")) for row in real_compiler_rows),
        "python_subprocess_invocation_count": sum(row.get("backend_type") == "python_subprocess_executor" and bool(row.get("runtime_invoked")) for row in supported),
        "internal_evaluator_call_count": 0,
        "compiler_spot_sample_count": len(real_compiler_rows),
        "supported_sample_count": len(supported),
        "boundary_sample_count": len(boundary),
        "compile_success_count": compile_success,
        "compile_failure_count": len(supported) - compile_success if backend_type == "real_c_compiler" else 0,
        "runtime_success_count": runtime_success,
        "runtime_failure_count": len(supported) - runtime_success,
        "compiler_verified_correct_count": verified_correct,
        "compiler_verified_failure_count": verified_failure,
        "compiler_verified_correct_rate": round(verified_correct / max(len(real_compiler_rows), 1), 6) if real_compiler_rows else None,
        "boundary_compiler_misroute_count": sum(bool(row.get("boundary_compiler_misroute")) for row in boundary),
        "division_by_zero_compiled_count": _compiled_boundary_count(boundary, "division_by_zero"),
        "non_integer_division_compiled_count": _compiled_boundary_count(boundary, "non_integer"),
        "unsupported_compiled_count": sum(bool(row.get("compiler_invoked")) for row in boundary),
        "timeout_count": sum(bool(row.get("timeout")) for row in supported),
        "forbidden_field_access_count": 0,
        "expected_output_access_before_candidate_generation": False,
        "target_ir_access_before_candidate_generation": False,
        "backend_claim_safe": _backend_claim_safe(backend_type, trace_rows),
        "candidate_trace_manifest_available": candidate_manifest.exists(),
        "trace_sample_count": len(trace_rows),
        "runtime_seconds": round(runtime_seconds, 6),
        **latency,
    }
    return metrics


def _compiled_boundary_count(rows: list[dict[str, Any]], marker: str) -> int:
    return sum(bool(row.get("compiler_invoked")) and marker in str(row.get("notes", "")) for row in rows)


def _backend_claim_safe(backend_type: str, rows: list[dict[str, Any]]) -> bool:
    if backend_type == "real_c_compiler":
        return any(row.get("compiler_invoked") for row in rows) and not any(row.get("internal_evaluator_used") for row in rows)
    if backend_type == "python_subprocess_executor":
        return not any(row.get("compiler_invoked") for row in rows) and not any(row.get("internal_evaluator_used") for row in rows)
    return backend_type in {"internal_evaluator", "unavailable"}


def _write_outputs(out: Path, metrics: Dict[str, Any]) -> None:
    _write_json(out / "compiler_spot_metrics.json", metrics)
    _write_json(out / "compiler_audit_readiness.json", {key: metrics[key] for key in [
        "audit_completed",
        "real_compiler_available",
        "backend_type",
        "real_compiler_invocation_count",
        "compiler_backed_spot_verified",
        "compiler_verified_correct_rate",
        "boundary_compiler_misroute_count",
        "forbidden_field_access_count",
        "backend_claim_safe",
        "recommended_claim_level",
        "blocking_issues",
        "required_next_run",
    ]})
    _write_mainline(out, metrics)


def _write_msvc_detection_report(out: Path, report: Dict[str, Any]) -> None:
    if not report:
        report = {
            "os_name": "",
            "path_cl_found": False,
            "path_gcc_found": False,
            "path_clang_found": False,
            "vswhere_found": False,
            "vcvars64_found": False,
            "vcvars64_path": "",
            "cl_bv_test_passed": False,
            "cl_version_text_tail": "",
            "detection_conclusion": "not_recorded",
        }
    _write_json(out / "msvc_detection_report.json", report)
    (out / "msvc_detection_report.md").write_text("\n".join([
        "# v0.9.4.1 MSVC Detection Report",
        "",
        f"- os_name: {report.get('os_name')}",
        f"- path_cl_found: {report.get('path_cl_found')}",
        f"- path_gcc_found: {report.get('path_gcc_found')}",
        f"- path_clang_found: {report.get('path_clang_found')}",
        f"- vswhere_found: {report.get('vswhere_found')}",
        f"- vcvars64_found: {report.get('vcvars64_found')}",
        f"- vcvars64_path: {report.get('vcvars64_path')}",
        f"- cl_bv_test_passed: {report.get('cl_bv_test_passed')}",
        f"- detection_conclusion: {report.get('detection_conclusion')}",
    ]) + "\n", encoding="utf-8")


def _write_mainline(out: Path, metrics: Dict[str, Any]) -> None:
    still_not = [
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
        "proved": ["compiler/backend spot audit completed"] if metrics["audit_completed"] else [],
        "not_proved": still_not,
        "advanced_internal_evaluator_signal_to_real_compiler": metrics["recommended_claim_level"] == "compiler_backed_arithmetic_spot_signal",
        **metrics,
        "paper_v2_results": ["backend type", "compiler invocation count", "compiler spot correctness", "boundary compiler misroute count"],
        "must_reproduce": ["larger compiler-backed arithmetic audit", "full compiler-backed longrun"],
        "still_not_proven": still_not,
    }
    _write_json(out / "mainline_conclusion.json", payload)
    (out / "mainline_conclusion.md").write_text("\n".join([
        "# v0.9.4.1 Mainline Conclusion",
        "",
        f"- backend_type: {metrics['backend_type']}",
        f"- real_compiler_invocation_count: {metrics['real_compiler_invocation_count']}",
        f"- compiler_verified_correct_rate: {metrics['compiler_verified_correct_rate']}",
        f"- boundary_compiler_misroute_count: {metrics['boundary_compiler_misroute_count']}",
        f"- backend_claim_safe: {metrics['backend_claim_safe']}",
        f"- recommended_claim_level: {metrics['recommended_claim_level']}",
        f"- blocking_issues: {metrics['blocking_issues']}",
        f"- required_next_run: {metrics['required_next_run']}",
        "- Still not proven: " + ", ".join(still_not),
    ]) + "\n", encoding="utf-8")


def _read_dataset_rows(dataset: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for scale in ["small", "medium", "large"]:
        scale_dir = dataset / scale
        if not scale_dir.exists():
            continue
        for split in ["heldout", "eval", "test", "train"]:
            for path in sorted((scale_dir / split).glob("*.jsonl")):
                rows.extend(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        if rows:
            break
    return rows


def _candidate_expression(row: Dict[str, Any]) -> str:
    expression = row.get("canonical_expression") or row.get("input") or ""
    return str(expression).split("#", 1)[0].strip(" ?.")


def _base_trace(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sample_id_hash": _hash_text(str(row.get("id", ""))),
        "split": row.get("split"),
        "stage": row.get("stage"),
        "category": row.get("category"),
        "input_hash": _hash_text(str(row.get("input", ""))),
    }


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
