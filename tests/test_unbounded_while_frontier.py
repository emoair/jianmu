from jianmu.self_learning.darwinforge.unbounded_while_frontier import unbounded_while_contract


def test_unbounded_while_semantic_not_bounded_only():
    contract = unbounded_while_contract()
    assert contract["semantic_unbounded_while_supported"] is True
    assert contract["runtime_watchdog_limited"] is True
    assert contract["production_supported"] is False
