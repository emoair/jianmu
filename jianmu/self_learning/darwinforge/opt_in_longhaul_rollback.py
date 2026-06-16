from __future__ import annotations

import json
from pathlib import Path

from jianmu.self_learning.darwinforge.opt_in_rollback_audit import run_opt_in_rollback_audit


def run_longhaul_rollback_review(output_records: str | Path, cycles: int = 500, samples_per_cycle: int = 5) -> dict:
    base = run_opt_in_rollback_audit(output_records, cycles, samples_per_cycle)
    result = {
        "rollback_review_completed": True,
        "rollback_cycles": base["opt_in_rollback_cycles"],
        "rollback_cycle_pass_count": base["opt_in_cycle_pass_count"],
        "rollback_cycle_fail_count": base["opt_in_cycle_fail_count"],
        "opt_out_blocks_bridge_after_each_cycle": base["opt_out_blocks_bridge_after_each_cycle"],
        "default_profile_after_each_cycle_unchanged": base["default_profile_after_each_cycle_unchanged"],
        "arithmetic_baseline_after_each_cycle_clean": base["arithmetic_baseline_after_each_cycle_clean"],
        "production_flags_after_each_cycle_false": base["production_flags_after_each_cycle_false"],
        "rollback_state_leak_detected": not base["opt_out_blocks_bridge_after_each_cycle"],
        "rollback_review_passed": base["opt_in_rollback_passed"],
    }
    out = Path(output_records)
    (out / "longhaul_rollback_review.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result
