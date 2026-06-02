from jianmu.self_learning.darwinforge.turing_frontier_true_endurance import REFERENCE_RATES


def state_growth_scaleup_target_met(rate: float) -> bool:
    return rate >= 0.91 and rate >= REFERENCE_RATES["state_growth_success_rate"]
