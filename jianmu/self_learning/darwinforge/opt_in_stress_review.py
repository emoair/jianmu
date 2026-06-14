from __future__ import annotations

from jianmu.self_learning.darwinforge.opt_in_rollback_audit import run_opt_in_rollback_audit


def run_opt_in_stress_review(output_records, cycles: int = 20, samples_per_cycle: int = 2):
    return run_opt_in_rollback_audit(output_records, cycles, samples_per_cycle)
