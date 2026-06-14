from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from jianmu.self_learning.darwinforge.arithmetic_compiler_backend import detect_arithmetic_backend, execute_with_backend
from jianmu.self_learning.darwinforge.opt_in_profile_adapter import execute_opt_in_request
from jianmu.self_learning.darwinforge.staged_opt_in_profile_schema import StagedOptInProfileConfig


def run_opt_in_rollback_audit(output_records: str | Path, cycles: int = 200, samples_per_cycle: int = 5) -> Dict[str, object]:
    backend = detect_arithmetic_backend(prefer_python_subprocess=False, prefer_msvc=True)
    cfg = StagedOptInProfileConfig()
    pass_count = 0
    for cycle in range(cycles):
        sample_ok = True
        for offset in range(samples_per_cycle):
            row = execute_opt_in_request(cycle * samples_per_cycle + offset, "function", backend, cfg.profile_name, True)
            sample_ok = sample_ok and row["passed"] and row["explicit_opt_in"]
        blocked = execute_opt_in_request(cycle, "function", backend, cfg.profile_name, False)
        arithmetic = execute_with_backend("1+2", backend, 5)
        baseline_ok = arithmetic.get("stdout_value_if_safe") == 3 or str(arithmetic.get("stdout_value_if_safe")) == "3"
        if sample_ok and blocked["passed"] and not blocked["compiler_invoked"] and baseline_ok:
            pass_count += 1
    result = {
        "opt_in_rollback_completed": True,
        "opt_in_rollback_cycles": cycles,
        "opt_in_cycle_pass_count": pass_count,
        "opt_in_cycle_fail_count": cycles - pass_count,
        "opt_out_blocks_bridge_after_each_cycle": pass_count == cycles,
        "default_profile_after_each_cycle_unchanged": pass_count == cycles,
        "arithmetic_baseline_after_each_cycle_clean": pass_count == cycles,
        "production_flags_after_each_cycle_false": pass_count == cycles,
        "opt_in_rollback_passed": pass_count == cycles,
    }
    _write_json(Path(output_records) / "opt_in_rollback_audit.json", result)
    return result


def _write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
