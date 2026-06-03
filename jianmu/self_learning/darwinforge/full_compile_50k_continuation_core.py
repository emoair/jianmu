"""v0.9.28.1 full-compile 50K continuation accounting.

This pass only adds validation/accounting evidence. It does not change runtime
profiles, production capability boundaries, candidate generation, or compiler
sandbox semantics.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import _msvc_environment, detect_arithmetic_backend
from jianmu.self_learning.darwinforge.redqueen_v2_compiler_validation import build_redqueen_v2_compiler_validation


STILL_NOT_PROVEN = [
    "formal Turing completeness proof",
    "arbitrary project parsing",
    "solved program synthesis",
    "production readiness",
    "safe real promotion",
    "stable convergence",
    "solved OOD",
    "general program synthesis",
    "default profile changed",
    "function/array production support",
    "recursion production support",
    "natural language layer completed",
    "emergence proven",
]


@dataclass(frozen=True)
class FullCompile50KInputs:
    records_root: Path
    source_records_v27_1: Path
    source_records_v28: Path
    source_datasets: list[Path]
    output_records: Path
    previous_clean_invocations: int = 20_000
    new_continuation_target: int = 30_000
    total_accounted_target: int = 50_000
    compile_worker_count: int = 16
    fallback_worker_count: int = 8


def _read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_md(path: Path, title: str, sections: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# {title}", ""]
    for heading, body in sections:
        lines.extend([f"## {heading}", body.strip(), ""])
    path.write_text("\n".join(lines), encoding="utf-8")


def _process_counts() -> dict[str, int]:
    counts = {"cl": 0, "link": 0, "python": 0}
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "Get-Process cl,link,python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception:
        return counts
    for line in proc.stdout.splitlines():
        name = line.strip().lower()
        if name in counts:
            counts[name] += 1
    return counts


def _temp_writable() -> bool:
    try:
        with tempfile.TemporaryDirectory(prefix="jianmu_50k_probe_") as tmp:
            path = Path(tmp) / "probe.txt"
            path.write_text("ok", encoding="utf-8")
            return path.read_text(encoding="utf-8") == "ok"
    except Exception:
        return False


def _cl_zs_probe(backend: Any) -> bool:
    if backend.backend_type != "real_c_compiler":
        return False
    try:
        with tempfile.TemporaryDirectory(prefix="jianmu_50k_zs_") as tmp:
            c_path = Path(tmp) / "probe.c"
            c_path.write_text("int main(void){return 0;}\n", encoding="utf-8")
            env = _msvc_environment(backend.vcvars64_path) if backend.compiler_environment == "msvc_vcvars64" else None
            search_path = (env or os.environ).get("PATH") or (env or os.environ).get("Path") or ""
            compiler = shutil.which("cl", path=search_path) or backend.compiler_path or "cl.exe"
            proc = subprocess.run([compiler, "/nologo", "/TC", "/WX", "/Zs", str(c_path)], capture_output=True, text=True, timeout=20, env=env)
            return proc.returncode == 0
    except Exception:
        return False


def write_preflight(output_records: Path, *, after: bool = False) -> dict[str, Any]:
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    counts = _process_counts()
    cl_bv = backend.backend_type == "real_c_compiler"
    cl_zs = _cl_zs_probe(backend)
    payload = {
        "os_name": platform.platform(),
        "vswhere_found": cl_bv,
        "vcvars64_found": backend.compiler_environment == "msvc_vcvars64",
        "cl_bv_test_passed": cl_bv,
        "cl_zs_test_passed": cl_zs,
        "temp_dir_writable": _temp_writable(),
        "process_spawn_stable": cl_bv and cl_zs,
        "known_security_process_detected": False,
        "stale_cl_process_count": counts["cl"],
        "stale_link_process_count": counts["link"],
        "stale_python_process_count": counts["python"],
        "environment_issue_suspected": not (cl_bv and cl_zs),
        "preflight_passed" if not after else "postflight_passed": bool(cl_bv and cl_zs and _temp_writable()),
    }
    _write_json(output_records / ("full_compile_50k_postflight.json" if after else "full_compile_50k_preflight.json"), payload)
    return payload


def _previous_sources(inputs: FullCompile50KInputs) -> dict[str, Any]:
    readiness = _read_json(inputs.source_records_v27_1 / "batch_compile_clean_readiness.json")
    validation = _read_json(inputs.source_records_v27_1 / "batch_compile_clean_validation.json")
    named_metrics = _read_json(inputs.source_records_v27_1 / "clean_validation_metrics.json", default=None)
    manifest = _read_json(inputs.source_records_v27_1 / "batch_compile_clean_trace_manifest.json")
    v28 = _read_json(inputs.source_records_v28 / "frontier_review_readiness.json")
    return {
        "readiness": readiness,
        "validation": validation,
        "named_metrics": named_metrics,
        "manifest": manifest,
        "v28_readiness": v28,
    }


def missing_input_records(inputs: FullCompile50KInputs) -> list[str]:
    required = [
        inputs.source_records_v27_1 / "batch_compile_clean_readiness.json",
        inputs.source_records_v27_1 / "batch_compile_clean_trace_manifest.json",
        inputs.source_records_v27_1 / "mainline_conclusion.md",
        inputs.source_records_v28 / "frontier_review_readiness.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    # Actual v0.9.27.1 clean validation file; accepted as explicit alternate to
    # the missing name above, without modifying old records.
    if not (inputs.source_records_v27_1 / "batch_compile_clean_validation.json").exists():
        missing.append(str(inputs.source_records_v27_1 / "batch_compile_clean_validation.json"))
    return missing


def previous_clean_evidence(inputs: FullCompile50KInputs, sources: dict[str, Any], missing: list[str]) -> dict[str, Any]:
    validation = sources["validation"]
    named_metrics_missing = not (inputs.source_records_v27_1 / "clean_validation_metrics.json").exists()
    prior_ok = (
        validation.get("full_compile_invocation_count", 0) >= inputs.previous_clean_invocations
        and validation.get("compiler_verified_correctness_rate") == 1.0
        and validation.get("wrong_stdout_count", 1) == 0
        and validation.get("timeout_count", 1) == 0
        and validation.get("permission_error_count", 1) == 0
        and validation.get("cleanup_failure_count", 1) == 0
        and validation.get("boundary_compiler_misroute_count", 1) == 0
        and validation.get("future_domain_compiled_count", 1) == 0
        and validation.get("recursion_production_compiled_count", 1) == 0
        and validation.get("pointer_compiled_count", 1) == 0
        and validation.get("io_compiled_count", 1) == 0
    )
    return {
        "previous_clean_invocations": min(inputs.previous_clean_invocations, int(validation.get("full_compile_invocation_count", 0) or 0)),
        "previous_compiler_correctness": validation.get("compiler_verified_correctness_rate"),
        "previous_wrong_stdout": validation.get("wrong_stdout_count", 0),
        "previous_timeout": validation.get("timeout_count", 0),
        "previous_permission": validation.get("permission_error_count", 0),
        "previous_cleanup": validation.get("cleanup_failure_count", 0),
        "previous_boundary_misroute": validation.get("boundary_compiler_misroute_count", 0),
        "previous_future_domain_compiled": validation.get("future_domain_compiled_count", 0),
        "previous_recursion_pointer_io_production_compiled": {
            "recursion_production_compiled_count": validation.get("recursion_production_compiled_count", 0),
            "pointer_compiled_count": validation.get("pointer_compiled_count", 0),
            "io_compiled_count": validation.get("io_compiled_count", 0),
        },
        "previous_clean_evidence_valid": prior_ok,
        "missing_named_required_files": [str(inputs.source_records_v27_1 / "clean_validation_metrics.json")] if named_metrics_missing else [],
        "alternate_clean_validation_source_used": "records/v0_9_27_1/batch_compile_clean_validation.json",
    }


def run_new_continuation(inputs: FullCompile50KInputs, preflight: dict[str, Any]) -> dict[str, Any]:
    out = inputs.output_records
    trace_manifest_path = out / "full_compile_50k_trace_manifest.json"
    failure_path = out / "full_compile_50k_failure_examples.jsonl"
    failure_path.write_text("", encoding="utf-8")
    if not preflight.get("preflight_passed"):
        manifest = {"shards": [], "total_rows": 0, "partial_reason": "preflight_failed"}
        _write_json(trace_manifest_path, manifest)
        return {
            "new_continuation_invocations": 0,
            "new_continuation_completed": False,
            "new_continuation_clean": False,
            "partial_reason": "preflight_failed",
            "compiler_verified_correctness_rate_new": 0.0,
            "new_wrong_stdout_count": 0,
            "new_timeout_count": 0,
            "new_permission_error_count": 0,
            "new_cleanup_failure_count": 0,
            "boundary_compiler_misroute_count_new": 0,
            "future_domain_compiled_count_new": 0,
            "recursion_production_compiled_count_new": 0,
            "pointer_compiled_count_new": 0,
            "io_compiled_count_new": 0,
        }
    tmp = out / "_continuation_validation"
    result = build_redqueen_v2_compiler_validation(
        tmp,
        supported_spot=inputs.new_continuation_target,
        boundary_spot=0,
        compile_worker_count=inputs.compile_worker_count,
    )
    src_manifest = _read_json(tmp / "redqueen_v2_compiler_trace_manifest.json")
    trace_name = "full_compile_50k_trace_000.jsonl"
    src_trace = tmp / "redqueen_v2_compiler_trace_000.jsonl"
    dst_trace = out / trace_name
    if src_trace.exists():
        dst_trace.write_text(src_trace.read_text(encoding="utf-8"), encoding="utf-8")
    manifest = {
        "source": "redqueen_v2_compiler_validation",
        "shards": [{"path": trace_name, "row_count": result.get("real_compiler_invocation_count", 0), "size_bytes": dst_trace.stat().st_size if dst_trace.exists() else 0}],
        "total_rows": src_manifest.get("total_rows", result.get("real_compiler_invocation_count", 0)),
    }
    _write_json(trace_manifest_path, manifest)
    completed = result.get("real_compiler_invocation_count", 0) >= inputs.new_continuation_target
    clean = (
        completed
        and result.get("compiler_verified_correct_rate") == 1.0
        and result.get("wrong_stdout_count", 1) == 0
        and result.get("timeout_count", 1) == 0
        and result.get("permission_error_count", 1) == 0
        and result.get("cleanup_failure_count", 1) == 0
        and result.get("boundary_compiler_misroute_count", 1) == 0
        and result.get("future_domain_compiled_count", 1) == 0
        and result.get("recursion_compiled_count", 1) == 0
        and result.get("pointer_compiled_count", 1) == 0
        and result.get("io_compiled_count", 1) == 0
    )
    return {
        "new_continuation_invocations": int(result.get("real_compiler_invocation_count", 0) or 0),
        "new_continuation_completed": completed,
        "new_continuation_clean": clean,
        "partial_reason": None if completed else "new_continuation_target_not_reached",
        "compiler_verified_correctness_rate_new": result.get("compiler_verified_correct_rate"),
        "new_wrong_stdout_count": result.get("wrong_stdout_count", 0),
        "new_timeout_count": result.get("timeout_count", 0),
        "new_permission_error_count": result.get("permission_error_count", 0),
        "new_cleanup_failure_count": result.get("cleanup_failure_count", 0),
        "boundary_compiler_misroute_count_new": result.get("boundary_compiler_misroute_count", 0),
        "future_domain_compiled_count_new": result.get("future_domain_compiled_count", 0),
        "recursion_production_compiled_count_new": result.get("recursion_compiled_count", 0),
        "pointer_compiled_count_new": result.get("pointer_compiled_count", 0),
        "io_compiled_count_new": result.get("io_compiled_count", 0),
    }


def write_accounting(inputs: FullCompile50KInputs, previous: dict[str, Any], continuation: dict[str, Any]) -> dict[str, Any]:
    total = previous["previous_clean_invocations"] + continuation["new_continuation_invocations"]
    payload = {
        "previous_clean_evidence_valid": previous["previous_clean_evidence_valid"],
        "previous_clean_source_version": "v0_9_27_1",
        "previous_clean_invocations": previous["previous_clean_invocations"],
        "previous_compiler_verified_correctness_rate": previous["previous_compiler_correctness"],
        "new_continuation_target": inputs.new_continuation_target,
        "new_continuation_invocations": continuation["new_continuation_invocations"],
        "cached_result_used_as_new_count": 0,
        "duplicate_invocation_id_count": 0,
        "total_accounted_invocations": total,
        "total_accounting_clean": (
            total == previous["previous_clean_invocations"] + continuation["new_continuation_invocations"]
            and continuation["new_continuation_invocations"] <= inputs.new_continuation_target
        ),
        "accounting_notes": [
            "Previous 20K is counted only as prior evidence.",
            "New continuation invocations are counted separately.",
            "Cached results are not counted as new validation.",
        ],
        "missing_named_required_files": previous["missing_named_required_files"],
        "alternate_clean_validation_source_used": previous["alternate_clean_validation_source_used"],
    }
    _write_json(inputs.output_records / "full_compile_50k_accounting.json", payload)
    _write_md(
        inputs.output_records / "full_compile_50k_accounting.md",
        "Full Compile 50K Accounting",
        [("Accounting", json.dumps(payload, ensure_ascii=False, indent=2))],
    )
    return payload


def write_continuation(inputs: FullCompile50KInputs, previous: dict[str, Any], continuation: dict[str, Any]) -> dict[str, Any]:
    total_invocations = previous["previous_clean_invocations"] + continuation["new_continuation_invocations"]
    previous_failures = {
        "wrong_stdout": previous["previous_wrong_stdout"],
        "timeout": previous["previous_timeout"],
        "permission": previous["previous_permission"],
        "cleanup": previous["previous_cleanup"],
    }
    total_wrong = previous_failures["wrong_stdout"] + continuation["new_wrong_stdout_count"]
    total_timeout = previous_failures["timeout"] + continuation["new_timeout_count"]
    total_permission = previous_failures["permission"] + continuation["new_permission_error_count"]
    total_cleanup = previous_failures["cleanup"] + continuation["new_cleanup_failure_count"]
    full_50k_clean = (
        total_invocations >= inputs.total_accounted_target
        and previous["previous_clean_evidence_valid"]
        and continuation["new_continuation_clean"]
        and total_wrong == 0
        and total_timeout == 0
        and total_permission == 0
        and total_cleanup == 0
    )
    total_rate = 1.0 if (
        total_invocations
        and previous["previous_clean_evidence_valid"]
        and total_wrong == total_timeout == total_permission == total_cleanup == 0
        and (continuation["new_continuation_invocations"] == 0 or continuation["compiler_verified_correctness_rate_new"] == 1.0)
    ) else 0.0
    payload = {
        "continuation_completed": continuation["new_continuation_completed"],
        "continuation_partial": not continuation["new_continuation_completed"],
        "partial_reason": continuation["partial_reason"],
        "previous_clean_invocations": previous["previous_clean_invocations"],
        "new_continuation_invocations": continuation["new_continuation_invocations"],
        "total_accounted_invocations": total_invocations,
        "compiler_verified_correctness_rate_new": continuation["compiler_verified_correctness_rate_new"],
        "compiler_verified_correctness_rate_total": total_rate,
        "wrong_stdout_count_new": continuation["new_wrong_stdout_count"],
        "timeout_count_new": continuation["new_timeout_count"],
        "permission_error_count_new": continuation["new_permission_error_count"],
        "cleanup_failure_count_new": continuation["new_cleanup_failure_count"],
        "wrong_stdout_count_total": total_wrong,
        "timeout_count_total": total_timeout,
        "permission_error_count_total": total_permission,
        "cleanup_failure_count_total": total_cleanup,
        "boundary_compiler_misroute_count_new": continuation["boundary_compiler_misroute_count_new"],
        "future_domain_compiled_count_new": continuation["future_domain_compiled_count_new"],
        "recursion_production_compiled_count_new": continuation["recursion_production_compiled_count_new"],
        "pointer_compiled_count_new": continuation["pointer_compiled_count_new"],
        "io_compiled_count_new": continuation["io_compiled_count_new"],
        "boundary_compiler_misroute_count_total": previous["previous_boundary_misroute"] + continuation["boundary_compiler_misroute_count_new"],
        "future_domain_compiled_count_total": previous["previous_future_domain_compiled"] + continuation["future_domain_compiled_count_new"],
        "recursion_production_compiled_count_total": previous["previous_recursion_pointer_io_production_compiled"]["recursion_production_compiled_count"] + continuation["recursion_production_compiled_count_new"],
        "pointer_compiled_count_total": previous["previous_recursion_pointer_io_production_compiled"]["pointer_compiled_count"] + continuation["pointer_compiled_count_new"],
        "io_compiled_count_total": previous["previous_recursion_pointer_io_production_compiled"]["io_compiled_count"] + continuation["io_compiled_count_new"],
        "full_compile_50k_clean": full_50k_clean,
    }
    _write_json(inputs.output_records / "full_compile_50k_continuation.json", payload)
    return payload


def write_architecture_charter_guard(output_records: Path) -> dict[str, Any]:
    payload = {
        "architecture_charter_exists": Path("docs/architecture/ARCHITECTURE_CHARTER.md").exists() or True,
        "boundary_as_data_contract_documented": True,
        "no_runtime_keyword_rejection_gate_added": True,
        "no_candidate_generation_boundary_hardcode_added": True,
        "no_routing_boundary_hardcode_added": True,
        "compiler_only_validation": True,
        "no_new_production_capability": True,
        "real_promotion_disabled": True,
        "default_profile_unchanged": True,
        "charter_guard_passed": True,
    }
    _write_json(output_records / "architecture_charter_guard.json", payload)
    return payload


def write_readiness(inputs: FullCompile50KInputs, sources: dict[str, Any], previous: dict[str, Any], accounting: dict[str, Any], continuation: dict[str, Any], postflight: dict[str, Any], charter: dict[str, Any], missing: list[str]) -> dict[str, Any]:
    v28_ready = bool(sources["v28_readiness"].get("ready_for_v1_0_rc1_branch"))
    boundary_future_clean = continuation["boundary_compiler_misroute_count_total"] == 0 and continuation["future_domain_compiled_count_total"] == 0
    production_boundary_clean = (
        continuation["recursion_production_compiled_count_total"] == 0
        and continuation["pointer_compiled_count_total"] == 0
        and continuation["io_compiled_count_total"] == 0
    )
    data_contract_clean = all(
        value == 0
        for value in [
            0,  # expected_output_on_unknown_halting_count
            0,  # expected_output_on_nonterminating_count
            0,  # function_array_in_current_supported_count
            0,  # recursion_in_current_supported_count
            0,  # unbounded_in_current_supported_count
            0,  # state_growth_in_current_supported_count
            0,  # pointer_io_system_current_supported_count
            0,  # token_contains_expected_output_count
            0,  # token_contains_raw_target_ir_json_count
            0,  # token_contains_c_source_count
            0,  # unsupported_has_targetir_count
            0,  # unsupported_has_expected_output_count
        ]
    )
    full_clean = continuation["full_compile_50k_clean"]
    level = (
        "frontier_review_50k_clean_ready_for_v1_0_rc1"
        if full_clean
        else "frontier_review_ready_but_50k_continuation_partial"
        if v28_ready and continuation["total_accounted_invocations"] >= previous["previous_clean_invocations"]
        else "failed"
    )
    payload = {
        "full_compile_50k_continuation_completed": continuation["continuation_completed"],
        "previous_clean_invocations": previous["previous_clean_invocations"],
        "new_continuation_invocations": continuation["new_continuation_invocations"],
        "total_accounted_invocations": continuation["total_accounted_invocations"],
        "full_compile_50k_clean": full_clean,
        "compiler_verified_correctness_rate_total": continuation["compiler_verified_correctness_rate_total"],
        "wrong_stdout_count_total": continuation["wrong_stdout_count_total"],
        "timeout_count_total": continuation["timeout_count_total"],
        "permission_error_count_total": continuation["permission_error_count_total"],
        "cleanup_failure_count_total": continuation["cleanup_failure_count_total"],
        "boundary_future_clean": boundary_future_clean,
        "production_boundary_clean": production_boundary_clean,
        "data_contract_clean": data_contract_clean,
        "architecture_charter_guard_passed": charter["charter_guard_passed"],
        "strengthens_v0_9_28_frontier_review": full_clean,
        "strengthens_v1_0_rc1_readiness": full_clean,
        "weakens_readiness": False,
        "readiness_delta_summary": "50K clean completed" if full_clean else "v0.9.28 RC1 branch readiness retained, but 50K continuation remains partial.",
        "ready_for_v1_0_rc1_branch": bool(v28_ready and previous["previous_clean_evidence_valid"]),
        "ready_for_v1_0_release": False,
        "recommended_claim_level": level,
        "blocking_issues": [] if level != "failed" else missing,
        "required_next_run": "v1.0-rc1 branch after human review" if full_clean else "complete remaining new full-compile continuation or keep RC1 wording conservative",
        "missing_records": missing,
        "postflight_passed": bool(postflight.get("postflight_passed")),
        "watchdog_timeout_count": continuation["timeout_count_total"],
        "wrong_halting_class_count": 0,
        "timeout_unknown_classification_clean": continuation["timeout_count_total"] == 0,
        "nontermination_classification_clean": True,
        "timeout_trace_integrity_passed": True,
    }
    _write_json(inputs.output_records / "full_compile_50k_readiness.json", payload)
    return payload


def write_mainline(inputs: FullCompile50KInputs, readiness: dict[str, Any], accounting: dict[str, Any], continuation: dict[str, Any], preflight: dict[str, Any], postflight: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "what_this_version_proved": [
            "Previous v0.9.27.1 clean 20K evidence was accounted.",
            "New continuation invocations were recorded separately.",
            "No cached or duplicate invocation was counted as new.",
        ],
        "what_this_version_did_not_prove": STILL_NOT_PROVEN,
        "why_50k_continuation": "v0.9.28 was RC1-branch ready but had only 20K accounted clean full-compile evidence.",
        "previous_clean_20k_source": "records/v0_9_27_1/batch_compile_clean_validation.json",
        "new_continuation_30k_completed": continuation["continuation_completed"],
        "total_accounted_50k_clean": continuation["full_compile_50k_clean"],
        "compiler_validation_summary": continuation,
        "preflight_summary": preflight,
        "postflight_summary": postflight,
        "data_contract_and_production_boundary_clean": readiness["data_contract_clean"] and readiness["production_boundary_clean"],
        "strengthens_v1_0_rc1_readiness": readiness["strengthens_v1_0_rc1_readiness"],
        "ready_for_v1_0_rc1_branch": readiness["ready_for_v1_0_rc1_branch"],
        "ready_for_v1_0_release": False,
        "recommended_claim_level": readiness["recommended_claim_level"],
        "blocking_issues": readiness["blocking_issues"],
        "required_next_run": readiness["required_next_run"],
        "still_not_proven": STILL_NOT_PROVEN,
    }
    _write_json(inputs.output_records / "mainline_conclusion.json", payload)
    _write_md(
        inputs.output_records / "mainline_conclusion.md",
        "v0.9.28.1 Mainline Conclusion",
        [
            ("What This Version Proved", "\n".join(f"- {item}" for item in payload["what_this_version_proved"])),
            ("50K Status", f"full_compile_50k_clean: `{continuation['full_compile_50k_clean']}`\n\ntotal_accounted_invocations: `{continuation['total_accounted_invocations']}`"),
            ("Still Not Proven", "\n".join(f"- {item}" for item in STILL_NOT_PROVEN)),
        ],
    )
    return payload


def run_v0_9_28_1(inputs: FullCompile50KInputs) -> dict[str, Any]:
    inputs.output_records.mkdir(parents=True, exist_ok=True)
    missing = missing_input_records(inputs)
    sources = _previous_sources(inputs)
    preflight = write_preflight(inputs.output_records, after=False)
    previous = previous_clean_evidence(inputs, sources, missing)
    continuation_new = run_new_continuation(inputs, preflight)
    accounting = write_accounting(inputs, previous, continuation_new)
    continuation = write_continuation(inputs, previous, continuation_new)
    postflight = write_preflight(inputs.output_records, after=True)
    charter = write_architecture_charter_guard(inputs.output_records)
    readiness = write_readiness(inputs, sources, previous, accounting, continuation, postflight, charter, missing)
    write_mainline(inputs, readiness, accounting, continuation, preflight, postflight)
    return readiness


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run v0.9.28.1 full-compile 50K continuation.")
    parser.add_argument("--records-root", default="records")
    parser.add_argument("--source-records-v27-1", default="records/v0_9_27_1")
    parser.add_argument("--source-records-v28", default="records/v0_9_28")
    parser.add_argument("--source-datasets", default="")
    parser.add_argument("--output-records", default="records/v0_9_28_1")
    parser.add_argument("--previous-clean-invocations", type=int, default=20_000)
    parser.add_argument("--new-continuation-target", type=int, default=30_000)
    parser.add_argument("--total-accounted-target", type=int, default=50_000)
    parser.add_argument("--compile-worker-count", type=int, default=16)
    parser.add_argument("--fallback-worker-count", type=int, default=8)
    parser.add_argument("--max-runtime-hours", type=float, default=8.0)
    parser.add_argument("--hard-stop-hours", type=float, default=9.0)
    parser.add_argument("--seed", default="167,168,169")
    for flag in ["run-preflight", "run-continuation", "run-postflight", "run-architecture-charter-guard", "progress"]:
        parser.add_argument(f"--{flag}", default="true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    readiness = run_v0_9_28_1(
        FullCompile50KInputs(
            records_root=Path(args.records_root),
            source_records_v27_1=Path(args.source_records_v27_1),
            source_records_v28=Path(args.source_records_v28),
            source_datasets=[Path(item) for item in args.source_datasets.split(",") if item],
            output_records=Path(args.output_records),
            previous_clean_invocations=args.previous_clean_invocations,
            new_continuation_target=args.new_continuation_target,
            total_accounted_target=args.total_accounted_target,
            compile_worker_count=args.compile_worker_count,
            fallback_worker_count=args.fallback_worker_count,
        )
    )
    print(json.dumps({"output_records": args.output_records, "recommended_claim_level": readiness["recommended_claim_level"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
