from jianmu.self_learning.darwinforge.turing_frontier_recursion_scaleup import recursion_scaleup_target_met


def test_recursion_scaleup_target():
    assert recursion_scaleup_target_met(0.914)
    assert not recursion_scaleup_target_met(0.89)
