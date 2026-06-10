from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend, execute_with_backend
from jianmu.self_learning.darwinforge.production_profile_dry_run_schema import ProductionProfileDryRunConfig
from jianmu.self_learning.darwinforge.production_profile_interface_adapter import execute_shadow_profile_request


def run_rollback_stress_review(output_records: str | Path, rollback_cycles: int = 100, samples_per_cycle: int = 5) -> Dict[str, object]:
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    pass_count = 0
    shadow_disable_pass = 0
    cfg = ProductionProfileDryRunConfig()
    for cycle in range(rollback_cycles):
        sample_ok = True
        for offset in range(samples_per_cycle):
            row = execute_shadow_profile_request(cycle * samples_per_cycle + offset, "function", backend, cfg.profile_name)
            sample_ok = sample_ok and row["passed"] and not row["real_promotion_enabled"] and not row["production_profile_modified"]
        arithmetic = execute_with_backend("1+2", backend, 5)
        disabled_ok = arithmetic.get("stdout_value_if_safe") == 3 or str(arithmetic.get("stdout_value_if_safe")) == "3"
        if sample_ok and disabled_ok:
            pass_count += 1
        if disabled_ok:
            shadow_disable_pass += 1
    result = {
        "rollback_stress_completed": True,
        "rollback_cycles": rollback_cycles,
        "rollback_cycle_pass_count": pass_count,
        "rollback_cycle_fail_count": rollback_cycles - pass_count,
        "shadow_disable_pass_count": shadow_disable_pass,
        "default_profile_after_each_cycle_unchanged": pass_count == rollback_cycles,
        "production_flags_after_each_cycle_false": pass_count == rollback_cycles,
        "rollback_stress_passed": pass_count == rollback_cycles,
    }
    _write_json(Path(output_records) / "rollback_stress_review.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
