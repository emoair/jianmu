from jianmu.self_learning.darwinforge.turing_frontier_tokens import EXPECTED_ACTIONS, SUPPORT_STATUSES


def test_turing_frontier_schema_statuses():
    assert "experimental_unbounded_while" in SUPPORT_STATUSES
    assert "experimental_recursion" in SUPPORT_STATUSES
    assert "experimental_state_growth" in SUPPORT_STATUSES
    assert "isolate_timeout_unknown" in EXPECTED_ACTIONS
