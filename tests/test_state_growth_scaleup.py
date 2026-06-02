from jianmu.self_learning.darwinforge.turing_frontier_state_growth_scaleup import state_growth_scaleup_target_met


def test_state_growth_scaleup_target():
    assert state_growth_scaleup_target_met(0.916)
    assert not state_growth_scaleup_target_met(0.90)
