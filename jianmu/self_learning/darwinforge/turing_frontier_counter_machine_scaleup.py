from jianmu.self_learning.darwinforge.turing_frontier_true_endurance import REFERENCE_RATES


def counter_machine_scaleup_target_met(rate: float) -> bool:
    return rate >= 0.97 and rate >= REFERENCE_RATES["counter_machine_witness_success_rate"]
