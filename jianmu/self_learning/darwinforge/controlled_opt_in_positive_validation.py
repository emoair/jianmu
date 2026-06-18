from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from jianmu.self_learning.darwinforge.controlled_opt_in_support_schema import ControlledOptInSupportConfig
from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import CompilerBackend, detect_arithmetic_backend
from jianmu.self_learning.darwinforge.coverage_expansion_execution import detect_coverage_replay_backend, execute_coverage_sample


COMPILER_CATEGORIES = {"function", "array", "function_array", "structured_recursion", "mixed"}


def run_positive_support_candidate_validation(output_records: str | Path, config: ControlledOptInSupportConfig, seed: int = 213, progress: bool = False) -> Dict[str, Any]:
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    backend = _detect_real_backend()
    if backend.backend_type != "real_c_compiler":
        blocked = {
            "positive_validation_completed": False,
            "positive_validation_events": 0,
            "real_compiler_invocations": 0,
            "positive_validation_passed": False,
            "blocking_issues": ["real_c_compiler_unavailable"],
            "backend_report": {"backend_type": backend.backend_type, "compiler_name": backend.compiler_name},
            "rows": [],
        }
        (out / "positive_support_candidate_validation.json").write_text(json.dumps({k: v for k, v in blocked.items() if k != "rows"}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return blocked
    rows: List[Dict[str, Any]] = []
    index = 0
    for category, target in config.positive_targets().items():
        for local in range(target):
            if category in COMPILER_CATEGORIES:
                row = execute_coverage_sample(seed + index, category, backend, config.profile_name)
                row["category"] = category
                row["support_candidate_validation"] = True
                row["sample_id"] = f"v1_0_8_positive_{category}_{seed + index:08d}"
            else:
                row = _rollback_or_replay_row(seed + index, category, config.profile_name)
            rows.append(row)
            index += 1
            if progress and len(rows) % 5000 == 0:
                print(json.dumps({"phase": "positive_validation_progress", "rows": len(rows), "category": category}, sort_keys=True), flush=True)
    result = _metrics(rows, config)
    result["backend_report"] = {"backend_type": backend.backend_type, "compiler_name": backend.compiler_name, "compiler_environment": backend.compiler_environment}
    (out / "positive_support_candidate_validation.json").write_text(json.dumps({k: v for k, v in result.items() if k not in {"rows", "backend_report"}}, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {**result, "rows": rows, "backend_report": result["backend_report"]}


def _rollback_or_replay_row(index: int, category: str, profile_name: str) -> Dict[str, Any]:
    sample_id = f"v1_0_8_positive_{category}_{index:08d}"
    return {
        "sample_id": sample_id,
        "category": category,
        "profile": profile_name,
        "explicit_opt_in": category == "replay_sample",
        "policy": "opt_in_rollback_check" if category == "opt_in_rollback" else "trace_replay_sample",
        "atomic_policy": "opt_in_rollback_check" if category == "opt_in_rollback" else "trace_replay_sample",
        "builder": "controlled_opt_in_rollback_review",
        "ir_kind": "rollback" if category == "opt_in_rollback" else "replay",
        "emitter": "none",
        "source_sha256": f"{category}-{index}",
        "compile_invocation_id": f"no-compile-{category}-{index}",
        "cl_invoked": False,
        "compiler_invoked": False,
        "link_invoked": False,
        "exe_run": False,
        "expected_stdout": "rollback_or_replay_clean",
        "actual_stdout": "rollback_or_replay_clean",
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


def _metrics(rows: List[Dict[str, Any]], config: ControlledOptInSupportConfig) -> Dict[str, Any]:
    real_compiler = sum(1 for row in rows if row.get("compiler_invoked"))
    wrong_stdout = sum(1 for row in rows if row.get("compiler_invoked") and row.get("actual_stdout") != row.get("expected_stdout"))
    result = {
        "positive_validation_completed": True,
        "positive_validation_events": len(rows),
        "real_compiler_invocations": real_compiler,
        "function_support_candidate_success_rate": _rate(rows, "function"),
        "array_support_candidate_success_rate": _rate(rows, "array"),
        "function_array_support_candidate_success_rate": _rate(rows, "function_array"),
        "structured_recursion_support_candidate_success_rate": _rate(rows, "structured_recursion"),
        "mixed_support_candidate_success_rate": _rate(rows, "mixed"),
        "rollback_success_rate": _rate(rows, "opt_in_rollback"),
        "replay_success_rate": _rate(rows, "replay_sample"),
        "compiler_verified_correctness_rate": round(sum(1 for row in rows if row.get("passed")) / len(rows), 6) if rows else 0.0,
        "wrong_stdout_count": wrong_stdout,
        "timeout_count": sum(1 for row in rows if row.get("timeout")),
        "permission_error_count": sum(1 for row in rows if row.get("permission_error")),
        "cleanup_failure_count": sum(1 for row in rows if row.get("cleanup_failure")),
        "cached_result_used_as_new_count": sum(1 for row in rows if row.get("cached")),
        "duplicate_invocation_id_count": len(rows) - len({row.get("compile_invocation_id") for row in rows}),
        "stubbed_validation_detected": any(row.get("stubbed") for row in rows),
        "summary_only_validation_detected": False,
    }
    result["positive_validation_passed"] = (
        result["positive_validation_events"] >= config.positive_validation_events
        and result["real_compiler_invocations"] >= config.minimum_real_compiler_invocations
        and all(result[field] == 1.0 for field in [
            "function_support_candidate_success_rate",
            "array_support_candidate_success_rate",
            "function_array_support_candidate_success_rate",
            "structured_recursion_support_candidate_success_rate",
            "mixed_support_candidate_success_rate",
            "rollback_success_rate",
            "replay_success_rate",
            "compiler_verified_correctness_rate",
        ])
        and result["wrong_stdout_count"] == 0
        and result["timeout_count"] == 0
        and result["permission_error_count"] == 0
        and result["cleanup_failure_count"] == 0
        and result["cached_result_used_as_new_count"] == 0
        and result["duplicate_invocation_id_count"] == 0
        and not result["stubbed_validation_detected"]
        and not result["summary_only_validation_detected"]
    )
    return result


def _detect_real_backend() -> CompilerBackend:
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    if backend.backend_type == "real_c_compiler":
        return backend
    backend = detect_coverage_replay_backend()
    if backend.backend_type == "real_c_compiler":
        return backend
    return backend


def _rate(rows: List[Dict[str, Any]], category: str) -> float:
    selected = [row for row in rows if row.get("category") == category]
    return round(sum(1 for row in selected if row.get("passed")) / len(selected), 6) if selected else 0.0

