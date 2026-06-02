from jianmu.self_learning.darwinforge.turing_frontier_counter_machine_scaleup import counter_machine_scaleup_target_met


def test_counter_machine_scaleup_target():
    assert counter_machine_scaleup_target_met(0.972)
    assert not counter_machine_scaleup_target_met(0.94)
