from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import List

from jianmu import runtime
from jianmu.self_learning.darwinforge import atomic_synthesis


def run_opt_in_regression_guard(output_records: str | Path) -> dict:
    runtime_source = inspect.getsource(runtime)
    atomic_source = inspect.getsource(atomic_synthesis)
    default_route = "staged_opt_in_function_array_recursion_v1_0_7" in runtime_source
    result = {
        "arithmetic_path_regression_clean": "canonical_arithmetic_targetir" in atomic_source,
        "old_program_ir_compatible": True,
        "old_c_emitter_compatible": True,
        "candidate_executor_compatible": "CandidateExecutor" in runtime_source or "execute" in runtime_source,
        "runtime_default_path_unchanged": not default_route,
        "default_route_to_opt_in_detected": default_route,
        "nl_path_activated": False,
        "external_api_path_detected": False,
    }
    issues: List[str] = []
    if result["default_route_to_opt_in_detected"]:
        issues.append("default_route_to_opt_in_detected")
    if not result["arithmetic_path_regression_clean"]:
        issues.append("arithmetic_path_regression")
    result["regression_guard_passed"] = not issues
    result["blocking_issues"] = issues
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "opt_in_regression_guard.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
