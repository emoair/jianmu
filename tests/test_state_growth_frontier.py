from jianmu.self_learning.darwinforge.state_growth_frontier import state_growth_contract


def test_state_growth_frontier_experimental_only():
    contract = state_growth_contract()
    assert contract["counter_registers"] is True
    assert contract["register_machine_state"] is True
    assert contract["production_supported"] is False
