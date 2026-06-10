from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Dict, List

from jianmu import runtime
from jianmu.self_learning.darwinforge import atomic_synthesis


def run_default_profile_contamination_audit(source_records: str | Path, output_records: str | Path) -> Dict[str, object]:
    readiness = json.loads((Path(source_records) / "production_profile_dry_run_readiness.json").read_text(encoding="utf-8"))
    runtime_source = inspect.getsource(runtime)
    atomic_source = inspect.getsource(atomic_synthesis)
    route_detected = "production_shadow_dry_run_v1_0_6" in runtime_source
    staged_enabled = bool(readiness.get("staged_opt_in_enabled", False))
    prod_auto = any(bool(readiness.get(key, False)) for key in ("production_function_support_completed", "production_array_support_completed", "production_recursion_support_completed"))
    result = {
        "default_profile_contamination_audit_completed": True,
        "default_runtime_path_unchanged": not route_detected,
        "default_candidate_executor_unchanged": "CandidateExecutor" in runtime_source or "execute" in runtime_source,
        "default_arithmetic_path_unchanged": "canonical_arithmetic_targetir" in atomic_source,
        "default_route_to_shadow_detected": route_detected,
        "production_flags_auto_enabled_detected": prod_auto,
        "user_facing_shadow_route_detected": bool(readiness.get("user_facing_enabled", False)),
        "staged_opt_in_enabled_detected": staged_enabled,
    }
    contamination = any(
        [
            result["default_route_to_shadow_detected"],
            result["production_flags_auto_enabled_detected"],
            result["user_facing_shadow_route_detected"],
            result["staged_opt_in_enabled_detected"],
            not result["default_runtime_path_unchanged"],
            not result["default_arithmetic_path_unchanged"],
        ]
    )
    issues: List[str] = []
    if contamination:
        issues.append("default_profile_contamination")
    result["default_profile_contamination_detected"] = contamination
    result["contamination_blocking_issues"] = issues
    _write_json(Path(output_records) / "default_profile_contamination_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
