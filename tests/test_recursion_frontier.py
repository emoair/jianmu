from jianmu.self_learning.darwinforge.recursion_frontier import recursion_contract


def test_recursion_frontier_experimental_only():
    contract = recursion_contract()
    assert contract["recursive_function_call_graph"] is True
    assert contract["recursion_depth_watchdog"] is True
    assert contract["production_supported"] is False
