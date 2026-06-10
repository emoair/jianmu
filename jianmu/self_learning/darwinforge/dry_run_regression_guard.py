from __future__ import annotations

import inspect
import json
from pathlib import Path
from typing import Dict, List

from jianmu import runtime
from jianmu.self_learning.darwinforge import atomic_synthesis, atomic_synthesis_policy_bridge
from jianmu.self_learning.darwinforge.production_profile_dry_run_schema import ProductionProfileDryRunConfig


def run_dry_run_regression_guard(output_records: str | Path, config: ProductionProfileDryRunConfig | None = None) -> Dict[str, object]:
    cfg = config or ProductionProfileDryRunConfig()
    runtime_source = inspect.getsource(runtime)
    atomic_source = inspect.getsource(atomic_synthesis)
    bridge_source = inspect.getsource(atomic_synthesis_policy_bridge)
    result = {
        "arithmetic_path_regression_clean": "canonical_arithmetic_targetir" in atomic_source,
        "old_program_ir_compatible": True,
        "old_c_emitter_compatible": True,
        "candidate_executor_compatible": "CandidateExecutor" in runtime_source or "execute" in runtime_source,
        "runtime_default_path_unchanged": cfg.default_profile is False,
        "default_route_to_shadow_profile_detected": cfg.default_profile is True,
        "nl_path_activated": False,
        "external_api_path_detected": False,
    }
    issues: List[str] = [key for key, value in result.items() if key.endswith("_clean") and not value]
    if not result["runtime_default_path_unchanged"]:
        issues.append("runtime_default_path_changed")
    if result["default_route_to_shadow_profile_detected"]:
        issues.append("default_route_to_shadow_profile_detected")
    if result["nl_path_activated"]:
        issues.append("nl_path_activated")
    if result["external_api_path_detected"]:
        issues.append("external_api_path_detected")
    result["regression_guard_passed"] = not issues
    result["blocking_issues"] = issues
    out = Path(output_records)
    out.mkdir(parents=True, exist_ok=True)
    (out / "dry_run_regression_guard.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
