from jianmu.self_learning.darwinforge.turing_frontier_true_endurance import REFERENCE_RATES


def recursion_scaleup_target_met(rate: float) -> bool:
    return rate >= 0.91 and rate >= REFERENCE_RATES["recursion_success_rate"]
